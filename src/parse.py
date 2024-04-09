from pypdf import PdfReader
import re
import json  # Import json librar
month=['01','02','03','04','05','06','07','08','09','10','11','12']
week=['MON','TUE','WED','THU','FRI','SAT',"SUN"]
text_list=[]
incident_line_start=[]
lines_cleaned=[]
Page_line_number=-1

Date_start=0
Location_length=27  # Max length for "Location" field. "Disposition" field has same max length.
Offense_length=27   # Max length for "Offense" field
import re
more_than_4_spaces=re.compile('\s\s\s\s\s*')  # pattern for ">=4 spaces"

# From this line(curr_index), at this index in string(start),
# scan the next a few lines until
# 1) the next line is empty, OR
# 2) it reaches the next_line_number, which means the next row
# and concat them all together. It can be used to extract a multiple-line cell.
def find_next_line(start,length,curr_index,string,next_line_number):
    global text_list
    c=1
    ans=string
    if length!=None:
        while len(text_list[curr_index+c][start:start+length].strip()) and curr_index+c<next_line_number:
            ans+=" "+text_list[curr_index+c][start:start+length].strip()
            c+=1
    else:
        while len(text_list[curr_index+c][start:].strip()) and curr_index+c<next_line_number:
            ans+=" "+text_list[curr_index+c][start:].strip()
            c+=1
    return ans

def remove_space_in_obj(obj):
    for k in obj.keys():
        obj[k]=obj[k].strip()
    return obj

def extract_row(row,line_number,next_line):
    global text_list
    row=row.strip()
    obj={}
    curr=0
    date_reported=row[0:14]+' '+text_list[line_number+1][0:8] # "Date Reported" is always 2 lines.
    obj['Date_reported']=date_reported
    F=re.search('\d\d-\d\d-\d\d-\d\d\d\d\d\d',row).span() # Find event number.
    event_number=row[F[0]:F[1]]
    obj['Event#']=event_number
    temp=row[F[1]:]
    case_number_exsit=re.match('\d\d\d\d\d\d\d',temp.lstrip()) # Check if case number exsits or not.
    if case_number_exsit:
        case_number=case_number_exsit.group(0)
        curr=row.index(case_number)+7
        F=re.finditer(more_than_4_spaces,row[curr:]) # Split the rest of line with the pattern "more than 4 spaces"
        zero_list=[]
        for f in F:
            zero_list.append(f.span())
        # The "Offense", "Init" and "Final" fields are always separate with more than 4 spaces.
        obj['Offense']=find_next_line(curr+zero_list[0][1],Offense_length,line_number,row[curr+zero_list[0][1]:curr+zero_list[1][0]],next_line)
        obj['Init']=find_next_line(curr + zero_list[1][1],Offense_length,line_number,row[curr + zero_list[1][1]:curr + zero_list[2][0]],next_line)
        # obj['Final']=find_next_line(curr+zero_list[2][1],Offense_length,line_number,row[curr + zero_list[2][1]:curr + zero_list[3][0]],next_line)
        curr=curr+zero_list[2][1]
        F=re.finditer(re.compile('\d\d/\d\d/\d\d'),row[curr:]) # Find time pattern. To find "Date from" and "Date to"
        time_list=[]
        for f in F:
            time_list.append(f.span())
        obj['DateFrom']=row[curr+time_list[0][0]:curr + time_list[1][0]]
        obj['DateTo']=row[curr + time_list[1][0]:curr + time_list[1][0] + 14]
        obj['Final'] = find_next_line(curr, Offense_length, line_number,
                                      row[curr:curr + time_list[0][0]], next_line)
        curr+=time_list[1][0]+14
        # Start finding "Location" and "Disposition"
        # They are normally separated by more than 4 spaces
        F=re.search(more_than_4_spaces,row[curr:])
        if F==None:
            # if not having "more than 4 spaces" pattern, dividing by max length
            obj['Location']=row[curr:curr+Location_length]
            obj['Disposition']=row[curr+Location_length:]
        elif F.span()[0]!=0:
            obj['Location']=row[curr:curr+F.span()[0]]
            obj['Disposition']=row[curr+F.span()[1]:]
        else:
            # "more than 4 spaces" not shown up at the front
            G=list(re.finditer(more_than_4_spaces,row[curr:]))
            if len(G)>1:
                obj['Location']=row[curr+G[0].span()[1]:curr+G[1].span()[0]]
                obj['Disposition']=row[curr+G[1].span()[1]:]
            else:
                curr+=G[0].span()[1]
                seperation=row[curr:].find('-') if row[curr:].find('-')>0 else Location_length-1
                obj['Location'] = row[curr - G[0].span()[1]:curr+seperation+1]
                obj['Disposition']=row[curr+seperation+1:]
        # Find "Location" and "Disposition" at the second line of the row
        second_line=text_list[line_number+1].strip()
        F=re.finditer(re.compile('at \d\d:\d\d'),second_line)
        curr=list(F)[2].span()[1]
        F=re.finditer(more_than_4_spaces,second_line[curr:])
        F=list(F)
        if len(F)==1:
            curr=curr+F[0].span()[1]
            obj['Location']+=' '+find_next_line(curr,Location_length,line_number+1,second_line[curr:],next_line)
        if len(F)>1:
            curr = curr + F[0].span()[1]
            obj['Location'] += ' ' + find_next_line(curr, Location_length, line_number + 1, second_line[curr:curr-F[0].span()[1]+F[1].span()[0]],next_line)
            obj['Disposition'] += ' ' + find_next_line(curr - F[0].span()[1] + F[1].span()[1], None, line_number + 1,
                                                       second_line[curr - F[0].span()[1] + F[1].span()[1]:], next_line)

    else:
        case_number=' '
        obj['Offense']=' '
        curr=30
        F = re.finditer(more_than_4_spaces, row[curr:])
        zero_list = []
        for f in F:
            zero_list.append(f.span())
        obj['Init'] = find_next_line(curr + zero_list[0][1], Offense_length, line_number,
                                        row[curr + zero_list[0][1]:curr + zero_list[1][0]], next_line)

        curr=curr+zero_list[1][1]
        F = re.finditer(re.compile('\d\d/\d\d/\d\d'), row[curr:])
        time_list = []
        for f in F:
            time_list.append(f.span())
        obj['Final'] = find_next_line(curr, Offense_length, line_number,
                                     row[curr:curr + time_list[0][0]], next_line)
        obj['DateFrom']=row[curr+time_list[0][0]:curr + time_list[1][0]]
        obj['DateTo']=row[curr + time_list[1][0]:curr + time_list[1][0] + 14]
        curr += time_list[1][0] + 14
        F = re.search(more_than_4_spaces, row[curr:])
        if F==None:
            obj['Location']=row[curr:curr+Location_length]
            obj['Disposition']=row[curr+Location_length:]
        elif F.span()[0]!=0:
            obj['Location']=row[curr:curr+F.span()[0]]
            obj['Disposition']=row[curr+F.span()[1]:]
        else:
            G=list(re.finditer(more_than_4_spaces,row[curr:]))
            if len(G) > 1:
                obj['Location'] = row[curr + G[0].span()[1]:curr + G[1].span()[0]]
                obj['Disposition'] = row[curr + G[1].span()[1]:]
            else:
                curr += G[0].span()[1]
                seperation = row[curr:].find('-') if row[curr:].find('-') > 0 else Location_length - 1
                obj['Location'] = row[curr - G[0].span()[1]:curr + seperation + 1]
                obj['Disposition'] = row[curr + seperation + 1:]
        second_line = text_list[line_number + 1].strip()
        F = re.finditer(re.compile('at \d\d:\d\d'), second_line)
        curr = list(F)[2].span()[1]
        F = re.finditer(more_than_4_spaces, second_line[curr:])
        F = list(F)
        if len(F)==1:
            curr=curr+F[0].span()[1]
            obj['Location']+=' '+find_next_line(curr,Location_length,line_number+1,second_line[curr:],next_line)
        if len(F)>1:
            curr = curr + F[0].span()[1]
            obj['Location'] += ' ' + find_next_line(curr, Location_length, line_number + 1, second_line[curr:curr-F[0].span()[1]+F[1].span()[0]],next_line)
            obj['Disposition']+= ' '+find_next_line(curr-F[0].span()[1]+F[1].span()[1],None,line_number+1,second_line[curr-F[0].span()[1]+F[1].span()[1]:],next_line)

    obj['case#']=case_number
    obj=remove_space_in_obj(obj)
    return obj
# extract_row(row,line_number,next_line)

result=[]

def read_page(text,pagenum):
    global text_list
    global incident_line_start
    global Page_line_number
    text_list = []
    incident_line_start = []
    Page_line_number = -1
    text_list=text.split('\n')
    for i in range(len(text_list)):
        line = text_list[i].strip()
        if len(line) == 0:
            continue
        if line[0:2] in month:
            incident_line_start.append(i)
        if "Page" in line and "of" in line:
            Page_line_number = i
    for i in range(len(incident_line_start)):
        try:
            if i!=len(incident_line_start)-1:
                result.append(extract_row(text_list[incident_line_start[i]],incident_line_start[i],incident_line_start[i+1]))
            else:
                result.append(extract_row(text_list[incident_line_start[i]], incident_line_start[i], Page_line_number))
        except:
            print("An error occurred in page ",pagenum," row",i+1)



def read_all(filepath):
    reader = PdfReader(filepath)
    for i in range(len(reader.pages)):
        page=reader.pages[i]
        text = page.extract_text(extraction_mode="layout")
        if i==45:
            print("debug")
        read_page(text,i+1)

def write_to_csv(result,filename):
    import csv
    fields=['Date_reported','Event#','case#','Offense','Init','Final','DateFrom','DateTo','Location','Disposition']
    with open(filename,'w') as csv_file:
        writer=csv.DictWriter(csv_file,fields)
        writer.writeheader()
        writer.writerows(result)

def write_to_json(result):
    return json.dumps(result, indent=4) 

def read_all(filepath):
    reader = PdfReader(filepath)
    for i in range(len(reader.pages)):
        page = reader.pages[i]
        text = page.extract_text(extraction_mode="layout")
        if i == 45:
            print("debug")
        read_page(text, i + 1)

# Modify the call to the output function to use write_to_json instead of write_to_csv
#read_all('./source_pdfs/031924.pdf')
def read_and_parse(filepath):
    read_all(filepath)
    return write_to_json(result)
