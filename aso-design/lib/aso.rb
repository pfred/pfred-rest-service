
require 'json'
require 'bio'
require 'open-uri/cached'
require 'nokogiri'
require 'awesome_print'
require 'securerandom'
require 'tty-command'
require 'tty-file'


require_relative 'org'
require_relative 'seqdb'
require_relative 'bowtie'

module ASO

  class Seq

    attr_accessor :id, :seq, :source, :entry_id, :gene_id, :name, :org, :exons, :cdna_len

    def initialize id=nil
      @id = id
      @exons = []
    end

    def cdna_len
      @cdna_len || seq.length
    end

    def seq= seq
      @seq = seq.strip.upcase
    end

    def to_fasta
      ">%s | %s  %s (%s)\n%s" % [id, gene_id, name, org.name, seq]
    end

    def enumerate len=20
      $stderr.puts seq
      (0..seq.length - len).map do |k|
        aso = Aso.new entry_id, k + 1, seq[k, len]
        aso_min = k + 1
        aso_max = k + len
        aso.exon_bound = exons.select{|e| e.cover?(aso_min) || e.cover?(aso_max)}.size > 1
        aso
      end
    end

    def asos
      @asos ||= enumerate
    end

    def source_label
      case source
      when :refseq
        'RefSeq'
      when :ensembl
        'Ensembl'
      else
        raise
      end
    end

  end

  class Aso

    attr_accessor :id, :seq, :start, :cdna, :pos, :exon_bound, :orth_cdna_hits, :offt_cdna_hits

    def initialize seq_id, start, cdna
      @id = '%s_%04d' % [seq_id, start]
      @seq_id = seq_id
      @cdna = cdna.upcase
      @pos = start
      @orth_cdna_hits = []
      @offt_cdna_hits = []
    end

    def cdna_as
      @cdna_as ||= cdna.reverse.tr 'GCAT', 'CGTA'
    end

    def rna
      @rna ||= cdna.gsub 'T', 'U'
    end

    def rna_as
      @rna_as ||= rna.reverse.tr 'GCAU', 'CGUA'
    end

    def count_substr_as str
      cdna_as.scan(str.upcase).size
    end

    def orth_cdna_count org, mis
      orth_cdna_hits.select{|h| h.org_ug == org.to_sym && h.mis == mis}.map(&:gene_id).flatten.uniq.size
    end

    def offt_cdna_count org, mis
      offt_cdna_hits.select{|h| h.org_ug == org.to_sym && h.mis == mis}.map(&:gene_id).flatten.uniq.size
    end

    def to_fasta
      ">%s\n%s" % [id, cdna]
    end

  end

  class AlignHit
    attr_accessor :hit, :org_ug, :gene_id, :cdna_id, :mis, :build, :gene_type
  end

  class AsoDesign

    BOWTIE_INDEX_ALL_CDNA = '/data/aso/release-92/index/all_cdna_mapped'

    def seqdb
      @seqdb ||= SeqService.new
    end

    def bowtie
      @bowtie ||=Bowtie.new 
    end

    def initialize tmp_dir=nil

      @dir = tmp_dir || File.join(Dir.tmpdir, 'aso-design', SecureRandom.uuid)
      $stderr.puts '  base dir: %s' % @dir

      # raise 'dir exists: %s' % @dir if File.exist? @dir
      TTY::File.create_dir @dir
      files = Dir.glob @dir + '/*'
      TTY::File.remove_file files if !files.empty?

    end

    def run_design seq_id

      # get input seq
      seq_in = seqdb.fetch_seq seq_id

      $stderr.puts 'using base id: %s' % seq_in.entry_id
      @base_id = seq_in.entry_id

      # single transcript id as input, find parent gene id
      ensg_id, enst_id = seqdb.ensembl_find_gene_id seq_in.id

      # find orthologs using gene id
      ortho_ids = seqdb.ensembl_find_ortho_ids ensg_id

      # get all transcripts for each species
      seqs = seqdb.ensembl_fetch_seqs ortho_ids

      # fetch cnda seqs
      seqs.each do |seq|
        seqdb.ensembl_fetch_seq seq
      end

      open file_aso_seqs, 'w' do |file|
        file.puts seq_in.asos.map(&:to_fasta).join("\n")
      end

      open file_orth_cdna, 'w' do |file|
        seqs.each do |seq|
          file.puts ">#{seq.entry_id}_#{seq.gene_id}\n#{seq.seq}"
        end
      end

      open file_model_input, 'w' do |file|
        file.puts "parent_antisense_oligo,name"
        seq_in.asos.each do |aso|
          file.puts [aso.cdna_as, aso.id].join ','
        end
      end

      orth_cdna_hits = bowtie.onetime_align file_orth_cdna, file_aso_seqs
      seq_in.asos.each do |aso|
        aso.orth_cdna_hits = orth_cdna_hits[aso.id] || []
      end

      offt_hits = bowtie.indexed_align BOWTIE_INDEX_ALL_CDNA, file_aso_seqs, file_offt_cdna_btout
      seq_in.asos.each do |aso|
        aso.offt_cdna_hits = offt_hits[aso.id] || []
      end

      open file_asos_full, 'w' do |file|
        orgs = Org.all.map &:ug
        file.print "seq_id\taso_id\tpos\tcdna\tcdna_antisense\texon_bound\tnum_tcc\tnum_tcg"
        orgs.each do |org|
          (0..3).each{|mis| file.print "\torth_#{org}_#{mis}" }
        end
        orgs.each do |org|
          (0..3).each{|mis| file.print "\tofft_#{org}_#{mis}" }
        end
        file.puts
        seq_in.asos.each do |aso|
          file.print [
            seq_in.id, aso.id, aso.pos, aso.cdna, aso.cdna_as, aso.exon_bound,
            aso.count_substr_as('TCC'), aso.count_substr_as('TCG')
          ].join("\t")
          orgs.each do |org|
            (0..3).each{|mis| file.print "\t#{aso.orth_cdna_count(org, mis)}" }
          end
          orgs.each do |org|
            (0..3).each{|mis| file.print "\t#{aso.offt_cdna_count(org, mis)}" }
          end
          file.puts
        end
      end

      open file_orth_cdna_hits, 'w' do |file|
        file.puts "aso_id\torg\tcdna_id\tgene_id\tnum_mismatch"
        seq_in.asos.each do |aso|
          aso.orth_cdna_hits.each do |hit|
            file.puts [aso.id, hit.org_ug, hit.cdna_id, hit.gene_id, hit.mis].join("\t")
          end
        end
      end

      open file_offt_cdna_hits, 'w' do |file|
        file.puts "aso_id\torg\tcdna_id\tgene_id\tnum_mismatch"
        seq_in.asos.each do |aso|
          aso.offt_cdna_hits.each do |hit|
            file.puts [aso.id, hit.org_ug, hit.cdna_id, hit.gene_id, hit.mis].join("\t")
          end
        end
      end

      $stderr.puts 'running property calculation'
      script_path = Pathname.new __dir__
      script_path += '../script/calculate_props.py'

      shell = TTY::Command.new dry_run: false
      shell.run 'python', script_path, file_asos_full, out: file_oligos

      $stderr.puts 'done.'
    end

    def base_file name
      File.join @dir, @base_id + '.' + name
    end

    def file_orth_cdna
      base_file 'orth_cdna.fa'
    end

    def file_model_input
      base_file 'predict.csv'
    end

    def file_orth_cdna_hits
      base_file 'orth_cdna_hits.txt'
    end

    def file_offt_cdna_btout
      base_file 'offt_cdna.bow'
    end

    def file_offt_cdna_hits
      base_file 'offt_cdna_hits.txt'
    end

    def file_aso_seqs
      base_file 'aso_seqs.fa'
    end

    def file_asos_full
      base_file 'asos.txt'
    end

    def file_oligos
      base_file 'oligos.csv'
    end

  end

end