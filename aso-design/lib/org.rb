module ASO

  class Org

    @orgs = []
    @index = nil

    attr_accessor :name, :ensg_db, :ug, :aliases

    def to_s
      '%s (%s)' % [name, ensg_db]
    end

    def self.all
      @orgs
    end

    def self.add name, ensg_db, ug, aliases=[]
      org = Org.new
      org.name = name
      org.ensg_db = ensg_db
      org.ug = ug.to_sym
      org.aliases = aliases
      @orgs.push org
    end

    def self.find name
      unless @index
        @index = Hash.new
        @orgs.map do |org|
          [org.name, org.ensg_db, org.ug, org.aliases].flatten.map do |key|
            @index[key.to_s.downcase.strip.gsub(/\s+/, '_')] = org
          end
        end
      end
      @index[name.to_s.downcase.strip.gsub(/\s+/, '_')]
    end

    # "ENSG00000185000",
    # "ENSMUSG00000022555",
    # "ENSRNOG00000028711",
    # "ENSMFAG00000003899"

    def self.for_ensg gene_id
      case gene_id
      when /^ENSG/
        find :hs
      when /^ENSMUS/
        find :mm
      when /^ENSRNO/
        find :rn
      when /^ENSMFA/
        find :mfa
      else
        raise 'unknown organism for gene: %s' % gene_id
      end
    end

    add 'Homo sapiens', :hsapiens, 'hs', ['human', '9606']
    add 'Mus musculus', :mmusculus, 'mm', ['mouse', '10090']
    add 'Rattus norvegicus', :rnorvegicus, 'rn', ['rat', '10116']
    add 'Macaca fascicularis', :mfascicularis, 'mfa', ['monkey', 'cyno', 'macaca', 'macaque', '9541']

  end

end