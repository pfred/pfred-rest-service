
require_relative '../lib/aso'

rest = ASO::SeqService.new

# get input seq
seq_in = rest.fetch_seq ARGV[0]

# single transcript id as input, find parent gene id
ensg_id, enst_id = rest.ensembl_find_gene_id seq_in.id

# find orthologs using gene id
ortho_ids = rest.ensembl_find_ortho_ids ensg_id

# get all transcripts for each species
seqs = rest.ensembl_fetch_seqs ortho_ids

seqs.reject! do |seq|
  flag = seq.id == enst_id
  $stderr.puts 'removing: %s (ensg equivalent of refseq input)' % seq.id if flag
  flag
end

seqs.each do |seq|
  rest.ensembl_fetch_seq seq
  puts seq.to_fasta
end

$stderr.puts 'done.'
