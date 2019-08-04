
class Bowtie

  # input in fasta, report all, up to 3 mismatches; suppress unneeded columns
  def cmd_align
    'bowtie -f -a -v3 --suppress 4,5,6,7 --threads 4'
  end

  # build an index of reference sequences ('refs') and align input sequences ('seqs') to it
  def onetime_align file_refs, file_seqs

    file_index = file_refs.sub /\.\w+$/, '.index'
    file_log = file_index + '.log'
    file_hits = file_refs.sub /\.\w+$/, '.bow'

    $stderr.puts "\n           building index: %s" % file_index.ai

    shell = TTY::Command.new dry_run: false
    shell.run 'bowtie-build', file_refs, file_index, out: file_log
    shell.run cmd_align, file_index, file_seqs, out: file_hits

    hits = parse_hits file_hits
    hits.each do |id, recs|
      recs.each do |rec|
        rec.cdna_id, rec.gene_id = rec.hit.split '_', 2
        org = ASO::Org.for_ensg rec.gene_id
        rec.org_ug = org.ug
        rec.hit = nil
      end
    end
    return hits

  end

  # align 'seqs' to pre-built index
  def indexed_align file_index, file_seqs, file_hits

    shell = TTY::Command.new dry_run: false
    shell.run cmd_align, file_index, file_seqs, out: file_hits

    hits = parse_hits file_hits
    hits.each do |id, recs|
      recs.each do |rec|
        rec.cdna_id, db_typ, rec.org_ug, rec.build, rec.gene_id, rec.gene_type = rec.hit.split '_', 6
        rec.org_ug = rec.org_ug.to_sym
        rec.hit = nil
      end
    end
    return hits
  end

  def parse_hits file
    hits = {}
    open(file).each_line.each do |line|
      id, strand, hit, mis = line.chomp.split /\t/, -1

      rec = ASO::AlignHit.new
      rec.hit = hit
      rec.mis = mis.split(',').size
      
      hits[id] ||= []
      hits[id].push rec
    end
    return hits
  end

end