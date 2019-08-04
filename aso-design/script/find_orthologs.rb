# ENST00000378474,Homo_sapiens,1889,ENSEMBL
# ENST00000336949,Homo_sapiens,2440,ENSEMBL
# ENSRNOT00000004305,Rattus_norvegicus,1902,ENSEMBL
# ENSMUST00000115524,Mus_musculus,2022,ENSEMBL
# ENSMUST00000008179,Mus_musculus,1922,ENSEMBL

require_relative '../lib/aso'

rest = ASO::SeqService.new

# get input seq
seq = rest.fetch_seq ARGV[0]

# single transcript id as input, find parent gene id
ensg_id, enst_id = rest.ensembl_find_gene_id seq.id

# find orthologs using gene id
ortho_ids = rest.ensembl_find_ortho_ids ensg_id

# get all transcripts for each species
recs = rest.ensembl_fetch_seqs ortho_ids

recs.unshift seq

recs.reject! do |seq|
  flag = seq.id == enst_id
  $stderr.puts 'removing: %s (ensg equivalent of refseq input)' % seq.id if flag
  flag
end

puts 'name,species,length,source'
recs.each do |rec|
  puts [rec.id, rec.org.name, rec.cdna_len, rec.source_label].join(',')
end

$stderr.puts 'done.'
