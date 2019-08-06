
# retrieve cdna sequences from genbank or ensembl
# fasta format

require_relative '../lib/aso'

rest = ASO::SeqService.new

ids = ARGV.map{|a| a.split(',')}.flatten.grep(/\w/)

ids.each do |id|
  $stderr.print "  find: '#{id}' ... "
  seq = rest.fetch_seq id

  if seq
    $stderr.puts 'found.'
    puts seq.to_fasta
  else
    $stderr.puts 'not found.'
  end

end
