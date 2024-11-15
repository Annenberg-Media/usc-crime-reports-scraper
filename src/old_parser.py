from pypdf import PdfReader
import re

date_pattern=re.compile('\d+/\d+/\d+')
time_pattern=re.compile('\d+:\d\d')
am_pm_pattern=re.compile('[ap]m')
report_number_pattern=re.compile('\d{7}')

# reader=PdfReader("010218.pdf")
#
# text_list=[]
#
# for page in reader.pages:
#     text = page.extract_text(extraction_mode="layout")
#     temp = text.split('\n')
#     for i in range(len(temp)):
#         t=temp[i].strip()
#         if t!="":
#             text_list.append(t)
# for i in range(len(text_list)):
#     text_list[i]=re.sub("\s\s+"," ",text_list[i])

def remove_unnecessary(text):
    if text=='University of Southern California' or text=='Department of Public Safety' or text=='Daily Incident Log':
        return False
    if text[0:4]=='From':
        return False
    return True

# text_list=list(filter(remove_unnecessary,text_list))
# report_rows=[]
#
#
# for i in range(len(text_list)):
#     if text_list[i][0:8]=='Reported':
#         report_rows.append(i)



def handle_report_row(text,obj):
    date=date_pattern.search(text)
    if date:
        date=date.group()
    else:
        raise ValueError('No Reported Date Info Found')
    time=time_pattern.search(text)
    if time:
        time=time.group()
    else:
        raise ValueError('No Reported Time Info Found')
    ampm=am_pm_pattern.search(text)
    if ampm:
        location_start=ampm.end()
        ampm=ampm.group()
    else:
        raise ValueError('No Reported Time Info Found')
    obj['reported']=date+" "+time+" "+ampm
    report_number=report_number_pattern.search(text)
    if report_number:
        location_end=report_number.start()-1
        report_number=report_number.group()
    else:
        raise ValueError('No Reported Number Info Found')
    obj['report number']=report_number
    obj['location']=text[location_start:location_end+1].strip()
    if "Location:" in obj['location']:
        obj['location']=obj['location'].replace("Location:","",1)
    if "Report #:" in obj['location']:
        obj['location'] = obj['location'].replace("Report #:", "", 1)


def handle_occur_row(text,obj):
    date_all=date_pattern.findall(text)
    time_all=time_pattern.findall(text)
    ampm_all=am_pm_pattern.findall(text)
    try:
        obj['start']=date_all[0]+" "+time_all[0]+" "+ampm_all[0]
        obj['end'] = date_all[1] + " " + time_all[1] + " " + ampm_all[1]
    except:
        raise ValueError("No Occurred Time Info Found")
    disposition_index=text.find("Disposition")
    if disposition_index==-1:
        raise ValueError("No Disposition Info Found")
    obj['disposition']=text[disposition_index+len("Disposition")+1:].strip()

def handle_incident(text,obj):
    if text.find("Incident")==-1:
        raise ValueError("No Incident Info Found")
    obj['incident']=text[len("Incident:"):].strip()

def handle_summary(text_list,current_index,next_report_index,obj):
    temp=text_list[current_index][len("Summary:"):].strip()
    j=current_index+1
    if next_report_index:
        while j<next_report_index:
            temp=temp+" "+text_list[j]
            j+=1
    else:
        while j<len(text_list):
            temp=temp+" "+text_list[j]
            j+=1
    obj['summary']=temp


def read_all(text_list,report_rows):
    result=[]
    for i in range(len(report_rows)):
        report_row_number=report_rows[i]
        obj={}
        try:
            handle_report_row(text_list[report_row_number],obj)
            j=1
            while text_list[report_row_number+j][0:8]!="Occurred":
                obj['location']=obj['location']+" "+text_list[report_row_number+j]
                j+=1
            handle_occur_row(text_list[report_row_number+j],obj)
            handle_incident(text_list[report_row_number+j+1],obj)
            if i!=len(report_rows)-1:
                handle_summary(text_list,report_row_number+j+2,report_rows[i+1],obj)
            else:
                handle_summary(text_list, report_row_number + j+2, None, obj)
            result.append(obj)
        except ValueError as e:
            print("Something wrong happened at case start with ",text_list[report_row_number])
            print(e)
    return result






def write_to_csv(result,filename):
    import csv
    fields=['reported','report number','location','start','end','disposition','incident','summary']
    with open(filename,'w') as csv_file:
        writer=csv.DictWriter(csv_file,fields)
        writer.writeheader()
        writer.writerows(result)


def read_pdf(pdf):
    reader=PdfReader(pdf)
    text_list = []
    for page in reader.pages:
        text = page.extract_text(extraction_mode="layout")
        temp = text.split('\n')
        for i in range(len(temp)):
            t = temp[i].strip()
            if t != "":
                text_list.append(t)
    for i in range(len(text_list)):
        text_list[i] = re.sub("\s\s+", " ", text_list[i])
    text_list = list(filter(remove_unnecessary, text_list))
    report_rows = []

    for i in range(len(text_list)):
        if text_list[i][0:8] == 'Reported':
            report_rows.append(i)
    return read_all(text_list,report_rows)
# r=read_pdf('121021.pdf')
# write_to_csv(r,"old2.csv")