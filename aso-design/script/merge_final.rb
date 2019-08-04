
require 'awesome_print'

main, pred = ARGV
$stderr.puts [main, pred].ai

f_main = open main
f_pred = open pred

puts f_main.gets.strip + ',' + f_pred.gets

preds = f_pred.read.split(/\n/).map{|r| [r.split(',', 2).first, r]}.to_h
f_pred.close
$stderr.puts preds.size.ai

f_main.each_line do |line|
  line = line.strip
  seq_id, id = line.split ',', 3
  pred_line = preds[id]
  raise id unless pred_line
  puts line + ',' + pred_line
end

f_main.close
