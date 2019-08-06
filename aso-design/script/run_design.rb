
require_relative '../lib/aso'

ad = ASO::AsoDesign.new ARGV[1]

ad.run_design ARGV[0]
