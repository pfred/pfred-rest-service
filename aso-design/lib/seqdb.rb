
module ASO

  class SeqService

    @@efetch_base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    @@mart_base = 'http://www.ensembl.org/biomart/martservice'

    @@enrest_find = 'https://rest.ensembl.org/lookup/id/%s?db_type=core&expand=0'

    def parse_fasta_rec fasta
      head, seq = fasta.split /\n/, 2
      head = head.sub(/^>/, '').strip.split(/\W/).first
      seq = seq.gsub(/\s+/, '').downcase
      [head, seq]
    end

    def fetch_seq seq_id
      if /^\w{2}_/ =~ seq_id
        ncbi_fetch_seq seq_id
      elsif /^ENS/ =~ seq_id
        ensembl_fetch_seq seq_id
      else
        raise 'unknown id type: ' + seq_id
      end
    end

    def ncbi_fetch_seq seq_id

      rec = Bio::FlatFile.open_uri "#{@@efetch_base}?db=nuccore&rettype=gb&retmode=text&id=#{seq_id}"
      rec = rec.next_entry.to_biosequence

      seq = Seq.new seq_id
      seq.source = :refseq
      seq.entry_id = rec.entry_id
      seq.name = rec.definition
      seq.org = Org.find rec.species
      seq.seq = rec.seq.downcase

      seq.gene_id = rec.features.select{|f| f.feature == 'gene'}.first['db_xref'].grep(/^GeneID/).first.split(':').last
      seq.exons = rec.features.select{|f| f.feature == 'exon'}.map{|f| f.locations.range}.to_a

      return seq
    end

    def ensembl_fetch_seq seq

      rows = ensembl_rest "#{seq.org.ensg_db}_gene_ensembl", [:ensembl_transcript_id, :cdna], ensembl_transcript_id: seq.entry_id, _format: :FASTA
      rec = parse_fasta_rec rows
      seq.seq = rec[1]
      
      raise unless rec[0] == seq.id

      rows = ensembl_rest "#{seq.org.ensg_db}_gene_ensembl", [:ensembl_transcript_id, :cdna_coding_start, :cdna_coding_end, :rank], ensembl_transcript_id: seq.entry_id
      seq.exons = rows.split(/\n/).map do |row|
        row = row.split /\t/
        raise unless row[0] == seq.entry_id
        next unless /\w/ =~ row[1]
        row[1].to_i .. row[2].to_i
      end.compact

      return seq
    end

    def ensembl_find_gene_id seq_id

      seq_id = seq_id.sub /\.\d+$/, ''
      rows = ensembl_rest 'hsapiens_gene_ensembl', [:ensembl_gene_id, :ensembl_transcript_id, :chromosome_name], refseq_mrna: seq_id
      ids = rows.split(/\n/).grep_v(/CHR_/)

      raise 'id not found: %s' % seq_id if ids.size == 0
      ap ids
      raise 'multiple genes for: %s' % seq_id if ids.size > 1

      return ids.first.split /\t/
    end


    def ensembl_find_ortho_ids gene_id
      orgs = [:mmusculus, :rnorvegicus, :mfascicularis]
      rows = ensembl_rest 'hsapiens_gene_ensembl', [:ensembl_gene_id] + orgs.map{|org| "#{org}_homolog_ensembl_gene"}, ensembl_gene_id: gene_id
      ids = rows.split /\s+/

      raise 'no orthologs found found: %s' % gene_id if ids.size == 0

      return ids
    end

    def ensembl_find_gene seq_id

      res = open @@enrest_find % seq_id, 'Content-Type' => 'application/json'
      rec = JSON.parse res.read, symbolize_names: true

      seq = Seq.new seq_id
      seq.source = :ensembl
      seq.entry_id = rec[:id]
      seq.name = rec[:display_name]
      seq.org = Org.find rec[:species]
      seq.gene_id = rec[:Parent]

      return seq
    end

    def ensembl_ensg_to_entrez gene_ids
      gene_ids.map do |gene_id|
        org = Org.for_ensg gene_id
        rows = ensembl_rest "#{org.ensg_db}_gene_ensembl", [:ensembl_gene_id, :entrezgene], ensembl_gene_id: gene_id
        rows.split(/\n/).map{|r| r.split /\t/}
      end.flatten(1).to_h
    end

    def ensembl_fetch_seqs gene_ids
      seqs = []
      gene_ids.each do |gene_id|
        org = Org.for_ensg gene_id
        rows = ensembl_rest "#{org.ensg_db}_gene_ensembl", [:ensembl_gene_id, :ensembl_transcript_id, :transcript_length], ensembl_gene_id: gene_id

        rows.split(/\n/).each do |row|
          row = row.split /\t/
          seq = Seq.new
          seq.gene_id = gene_id
          seq.org = org
          seq.source = :ensembl
          seq.id = row[1]
          seq.entry_id = row[1]
          seq.cdna_len = row[2].to_i
          seqs.push seq
        end

      end

      return seqs
    end

    def ensembl_find_ortho gene
      filter = { (gene.source == :refseq ? :entrezgene : :ensembl_gene_id) => gene.gene_id }
      orgs = [:mmusculus, :rnorvegicus, :mfascicularis]
      rows = ensembl_rest 'hsapiens_gene_ensembl', [:ensembl_gene_id] + orgs.map{|org| "#{org}_homolog_ensembl_gene"}, filter

      raise 'gene not found: ' + gene.gene_id if rows == ''

      # only one gene for transcript
      row = rows.split(/\n/).first
      row = row.split /\t/

      seqs = []
      hs = Seq.new
      hs.gene_id = row.first
      hs.source = :ensembl
      hs.org = Org.find 'hs'
      seqs.push hs

      row.drop(1).each_with_index do |id, idx|
        orth = Seq.new
        orth.gene_id = id
        orth.source = :ensembl
        orth.org = Org.find orgs[idx]
        seqs.push orth
      end

      return seqs
    end

    def ensembl_rest db, attrs=[], filters

      $stderr.puts 'biomart query: %s' % db

      fmt = filters.delete :_format || 'TSV'

      query = Nokogiri::XML::Builder.new do |doc|
        doc.Query(virtualSchemaName: 'default', formatter: fmt, header: 0, uniqueRows: 1, datasetConfigVersion: 0.6) do
          doc.Dataset(name: db, interface: 'default') do
            filters.each do |k,v|
              doc.Filter(name: k, value: v)
            end
            attrs.each do |attr|
              doc.Attribute name: attr
            end
          end
        end
      end.to_xml

      open("#{@@mart_base}?query=#{query.gsub(/\s+/, ' ').strip}").read

    end

  end

end