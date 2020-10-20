def region_str(chrom, start, end=None, strand=+1):
    """Assemble a region string suitable for consumption for the Ensembl REST API.
    
    The generated string has the format: ``{chrom}:{start}..{end}:{strand}``
    
    """
    if end is None:
        end = start
        
    return f'{chrom}:{start}..{end}:{strand}'
# --- 
