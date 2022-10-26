# eliminar lineas vacias del codigo
#import libraries
from importlib.metadata import files
from json import load
import pandas as pd
import os as os
import re as re
import glob
import sympy as spy
import sys
import math
from IPython.display import display, Latex

reserved_words = {"inicio","pare","si","sino","fsi","para","fpara"}
single_instructions = {"lea","esc",'si'}
path = './sample'

def file_test(file):
     
     files = os.listdir(path)
     paths = [os.path.join(path, basename) for basename in files]
     return max(paths, key=os.path.getctime)

def load_file(root):
    file_project = open (root, 'r', encoding='utf8')
    line_file = file_project.readlines()
    file_project.close()

    for line in range(0,len(line_file)):
        line_file[line] = line_file[line].replace("\n","")

    print('file has been uploaded', file_test(path))
    return line_file

def transform_lines(lines):
	return list(map(lambda x: x.lower().strip(), lines))



def validation_rules(line_file):
	if not line_file[0].lower() == 'inicio' or not line_file[-1].lower() == 'pare':
		return False
	for line in line_file:
		if not re.search('^[a-z]', line):
			sys.exit(f'error on line : {line}')
	return True

def mark_single_line_inst(lines, valid_words=single_instructions, reserved_words=reserved_words):
	lines_dict = []
	index = 0
	
	for line in lines:
		primer_espacio = re.split("\s", line)[0].strip()
		primer_igual = re.split("=", line)[0].strip()
		primer_espacio_igual = re.split("\s|=", line)[0].strip()

		if (primer_espacio in valid_words or 
        primer_igual.isidentifier() 
        and primer_espacio_igual not in reserved_words):
			value = 1
			if re.split("\s", line)[0] == 'si' and re.search("\)\s*[yo]\s*\(", line):
				value = 2
			lines_dict.append(value)
			#print(value, line)
			
		else:
			lines_dict.append(0)
		index+=1

	return lines_dict

def get_pair_paras(lines):
	paras = []
	stack = []
	index = 0
	for line in lines:
		if line.startswith('para'):
			stack.append(index)
		elif line.startswith('fpara'):
			start = stack.pop()
			paras.append((start, index))
		index+=1
	return paras

def get_si_pairs(lines):
	sis = []
	stack = []
	index = 0
	for line in lines:
		if line.startswith('si') and not line.startswith('sino'):
			stack.append((index,))
		elif line.startswith('sino'):
			start = stack.pop()
			stack.append((*start, index))
		elif line.startswith('fsi'):
			start = stack.pop()
			sis.append((*start, index))
		index+=1
	return sis

def is_inside(val, groups):
	for group in groups:
		if group[0] <= val < group[-1]:
			return True
	return False

def acumulate_outside_single_inst(lines_values, paras, sis):
	acum = 0
	index = 0
	new_line_values = []
	for line_value in lines_values:
		if not is_inside(index, paras) and not is_inside(index, sis):
			acum += line_value
			#print(index, line_value)
			new_line_values.append(0)
		else:
			new_line_values.append(line_value)
		index+=1
	return acum

def simplify_code(code,paras,sis,worst_cases):
	summary= []
	sis_summary= []
	parent_tracker = -1
	children_tracker = []
	value_tn = ''
	for index, si in enumerate(sis):
		parent_tracker = -1
		worst_case = worst_cases[index]
		for para_index in range(len(paras)):
			para = paras[para_index]
			is_child = si[0] > para[0] and si[-1] < para[1]
			if is_child:
				parent_tracker = para_index
				break
		sis_summary.append({'parent': parent_tracker, 'tn': worst_case, 'lines': si})


	for index,para in enumerate(paras):
		children_tracker = []
		parent_tracker = -1
		is_child = False
		if index + 1< len(paras):
			next_para = paras[index+1]
			is_child = para[0] > next_para[0] and para[1] < next_para[1]
			if is_child:
				parent_tracker = index+1
		if not is_child and (index+1 < len(paras)):
			for parent_index in range(index+1,len(paras)):
				next_para = paras[parent_index]
				is_child = para[0] > next_para[0] and para[1] < next_para[1]
				if is_child:
					parent_tracker = parent_index
					break
		for index_previous, previous in enumerate(summary):
			if previous['parent'] == index:
				children_tracker.append(index_previous)
		child_tn = 0
		raw_lines = list(range(para[0],para[1]+1))
		lines = list(zip(raw_lines,[1]*len(raw_lines)))
		lines[0] = (lines[0][0],0)
		lines[-1] = (lines[-1][0],0)
	
		for child_index in children_tracker:
			child_tn+= summary[child_index]['tn']
			#print(child_tn, summary[child_index]['tn'], child_index)
			child_para = paras[child_index]
			child_lines =  list(range(child_para[0],child_para[1]+1))
			for child_line in child_lines:
				lines[child_line-para[0]] = (child_line,0)
		child_si = 0
		for si_item in sis_summary:
			if si_item['parent'] == index:
				child_si+= si_item['tn']
				si = si_item['lines']
				child_lines =  list(range(si[0],si[-1]+1))
				for child_line in child_lines:
					lines[child_line-para[0]] = (child_line,0)

		
		tn_outside = 0
		for line_index,increment in lines:
			tn_outside += increment 
		
		para_start = para[0]
		statement = code[para_start]
		payload = statement.split(' ') [1].split(',')
		vf = payload[1]
		vi = payload[0].split('=')[1]
		delta = payload[2]
		if delta.startswith('-'):
			t = vf
			vf = vi
			vi = t
			delta = delta.replace('-', '')

		iteraciones = spy.simplify(f'({vf}-{vi}+1) / {delta}') 
		if str(iteraciones).isnumeric():
			iteraciones = int(math.ceil(iteraciones.evalf()))
		else:
			iteraciones = str(iteraciones)

		print(f'tn_{index}', f'({child_tn} + {tn_outside} +{child_si}+ 2)*({iteraciones})+ 2')
		tn = spy.simplify(f'({child_tn} + {tn_outside} +{child_si}+ 2)*({iteraciones})+ 2')
		#print(tn)
		if str(tn).isnumeric():
			tn = int(tn.evalf())
		else:
			tn = str(tn)
		summary.append({'parent': parent_tracker,'childs': children_tracker,'tn': tn, 'lines': paras[index]})
	for item in summary:
		if item['parent'] == -1:
			value_tn += f'+({item ["tn"]})'

	for item in sis_summary:
		if item['parent'] == -1:
			value_tn += f'+({item ["tn"]})'
	
	lines_blocks = 0

	for item in summary:
		if item['parent'] == -1:
			lines_within = item['lines']
			block_size = lines_within[-1] - lines_within[0] + 1
			lines_blocks += block_size

	for item in sis_summary:
		if item['parent'] == -1:
			lines_within = item['lines']
			block_size = lines_within[-1] - lines_within[0] + 1
			lines_blocks += block_size
	lines_outside = len(code) - 2 - lines_blocks
	value_tn += f'+({lines_outside})'
	#print(summary)
	#print(sis_summary)
	print(value_tn)
	value_tn = spy.simplify(value_tn)
	#print(value_tn)
	return value_tn


def acumulate_values(lines, lines_values, paras):
	acum = ""
	index = 0

	for para in paras:
		start_p = para[0]
		end_p = para[1]
		seccion_incremento = lines[start_p].split(" ")[1]
		start_value = seccion_incremento.split("=")[1].split(",")[0]
		end_value = seccion_incremento.split("=")[1].split(",")[1]
		value = sum(lines_values[start_p : end_p])
		if start_value.isnumeric():

			acum+= f"+ {value}*{end_value} + 2*{end_value} + 2 "
		else:
		
			acum+= f"+ {value}*{start_value} + 2*{start_value} + 2"
	return acum

def acumulate_sis(lines_values, sis):
	acum = 0
	index = 0
	for si in sis:
		acum+= sum(lines_values[si[0]:si[1]])
	return acum
	

def get_worst_cases(code,lines_values, sis):
	worst_cases = []
	for group in sis:
		if len(group) ==2:
			value = 1
			line = code[group[0]]
			if re.split("\s", line)[0] == 'si' and re.search("\)\s*[yo]\s*\(", line):
				value = 2
			#print('@ si')
			#print(value, len(lines_values[group[0]:group[1]+1])-2)
			value += len(lines_values[group[0]:group[1]+1])-2
			worst_cases.append(value)
		if len(group) > 2:
			value = 1
			line = code[group[0]]

			if re.split("\s", line)[0] == 'si' and re.search("\)\s*[yo]\s*\(", line):
				value = 2
			if sum(lines_values[group[0]:group[1]]) > sum(lines_values[group[1]:group[2]]):
				#print('@ si')
				#print(value, len(lines_values[group[0]:group[1]+1])-2)
				value += len(lines_values[group[0]:group[1]+1])-2
				
			else:
				#print('@ sino')
				#print(value, len(lines_values[group[1]:group[2]+1])-2)
				value += len(lines_values[group[1]:group[2]+1])-2
			worst_cases.append(value)

	return worst_cases

def main():
	root = file_test(path)
	lines = load_file(root)
	line_file = transform_lines(lines)
	print(line_file)
	print(validation_rules(line_file))
	
	if not validation_rules(line_file):
		sys.exit("error : file format")
	single_lines_values = mark_single_line_inst(line_file)
	#print(single_lines_values)
	paras = get_pair_paras(line_file)
	#print(paras)
	sis = get_si_pairs(line_file)
	#print(sis)
	#print('-----------')
	worst_cases = get_worst_cases(line_file, single_lines_values, sis)
	#print(worst_cases)
	#print('----------')
	tn_blocks = simplify_code(line_file, paras, sis,worst_cases)
	print('T(n) = ', tn_blocks)
 

if __name__ == '__main__':
    main()
    

    