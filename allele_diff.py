import string
import operator
import logging
from collections import defaultdict
from operator import itemgetter

class AlleleDiff:
  def __init__(self, allele_file="HLAB.txt"):
    self.alleles = self.parse_alleles(allele_file)

  def parse_alleles(self, allele_file):
    allele_definitions = {}
    with open(allele_file) as f:
      for i, line in enumerate(f):
        if i < 3:
          continue
        allele_def = line.split()
        allele_string = allele_def[1:]
        allele_definitions[allele_def[0]] = ["%s:%s" % (i, base) for i, base in enumerate(allele_string) if ('|' != base or '*' != base)]
    return allele_definitions
 
  def check_alleles(self, important, unimportant, snp_filter):
    logging.debug("In check_alleles.  Important: %s Filter: %s" % (important, snp_filter))
    important_alleles = self.filter_alleles(important, snp_filter)
    unimportant_alleles = self.filter_alleles(unimportant, snp_filter, True)
    remaining_important = [allele for allele in important if allele not in important_alleles]
    filtered_snps = [temp_snp['snp'] for temp_snp in snp_filter]
    if not important or len(important_alleles) == 0:
      return []
    logging.debug("Before recursion check.  snp_filter: %s important %s unimportant %s" % (snp_filter, important_alleles, unimportant_alleles))
    if len(snp_filter) > 0 and len(important_alleles) == 1 and len(unimportant_alleles) == 0:
      logging.debug("About to recurse.  important: %s remaining_important %s" % (important_alleles[0], remaining_important))
      return [{'allele': important_alleles[0], 'snps': filtered_snps}] + self.check_alleles(remaining_important, unimportant, [])
      
    all_alleles = important_alleles + unimportant_alleles
    snp_map = defaultdict(lambda: defaultdict(list))
    for allele in all_alleles:
      seq = self.alleles[allele]
      for item in seq:
        snp_map[item]['present'].append(allele)
        
    all_snp_scores = self.score_snps(important_alleles, unimportant_alleles, snp_map)
    for to_test in all_snp_scores:
      if to_test['snp'] not in filtered_snps:
        snp_filter.append(to_test)
        return self.check_alleles(important, unimportant, snp_filter)
    return []
  
  def filter_alleles(self, alleles, snp_filter, include=True):
    if len(snp_filter) < 1:
      return alleles
    to_filter = [snp['snp'] for snp in snp_filter]
    filtered_alleles = []
    if not include:
      filtered_alleles = list(alleles)
    for allele in alleles:
      seq = self.alleles[allele]
      if include and all([snp in seq for snp in to_filter]):
        filtered_alleles.append(allele)
      elif not include and not any([snp in seq for snp in to_filter]):
        filtered_alleles.remove(allele)

    return filtered_alleles
    
  def score_snps(self, important_alleles, unimportant_alleles, snp_map):
    all_snp_scores = []
    for snp, allele_map in snp_map.iteritems():
      
      important_snp_allele = [allele for allele in allele_map['present'] if allele in important_alleles]
      unimportant_snp_allele = [allele for allele in  allele_map['present'] if allele in unimportant_alleles]
      important_ratio = len(important_snp_allele) / float(len(important_alleles))
      unimportant_ratio = 0
      if len(unimportant_alleles) > 0:
        unimportant_ratio = len(unimportant_snp_allele) / float(len(unimportant_alleles))
      if important_ratio > 0:
        
        raw_score = important_ratio - unimportant_ratio + (0 if "_" in snp else 1)
        all_snp_scores.append({'snp': snp, 'score': raw_score})
        
    return sorted(all_snp_scores, key=itemgetter('score'), reverse=True)
  
if __name__ == "__main__":
  
  allele_diff = AlleleDiff()
  important_alleles = ['B*51240301', 'B*55070101']
  unimportant_alleles = [allele for allele in allele_diff.alleles.keys() if allele not in important_alleles]
  allele_mapping = allele_diff.check_alleles(important_alleles, unimportant_alleles, [])
  print allele_mapping
