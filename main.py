import json
import pdfplumber
import docx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os

# Configure Gemini
genai.configure(api_key="AIzaSyAZ7GTHvo3ttXPQtEHVtEsRemUMuXzTpTI" )




app = FastAPI()
app = FastAPI(title="Document Extractor API" )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.2.72:3000","http://localhost:3000","https://brsr-eight.vercel.app/"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)





KEYS_TO_EXTRACT = """

Corporate Identity Number (CIN) of the Listed Entity
Name of the Listed Entity
Year of incorporation
Registered office address
Corporate address		
Email
Telephone
Website
Financial year for which reporting is being done
Name of the Stock Exchange(s) where shares are listed
Paid-up Capital
Name and contact details
Reporting boundary - Are the disclosures under this report made on a standalone basis (i.e. only for the entity) or on a consolidated basis (i.e. for the entity and all the entities which form a part of its consolidated financial statements, taken together)
Name of assurance provider
Type of assurance obtained
Details of business activities (accounting for 90% of the turnover)
Products/Services sold by the entity (accounting for 90% of the entity’s Turnover):
No. of locations where plants and/or operations/ offices of the entity are situated:
Markets served by the entity
No. of Locations
What is the contribution of exports as a percentage of the total turnover of the entity?
Employees and workers (including differently abled):
Differently abled Employees and workers:
Participation/Inclusion/Representation of women
Turnover rate for permanent employees and workers (Disclose trends for the past 3 years)
How many products have undergone a carbon footprint assessment?
Whether CSR is applicable as per section 135 of Companies Act, 2013: (Yes/No)
Turnover (in Rs.)
Net worth (in Rs.)
Net worth (in Rs.)
Complaints/Grievances on any of the principles (Principles 1 to 9) under the National Guidelines on Responsible Business Conduct:
Please indicate material responsible business conduct and sustainability issues pertaining to environmental and social matters that present a risk or an opportunity to your business, rationale for identifying the same, approach to adapt or mitigate the risk along-with its financial implications, as per the following format.
Whether your entity’s policy/policies cover each principle and its core elements of the NGRBCs. (Yes/No)
Statement by director responsible for the business responsibility report, highlighting ESG related challenges, targets and achievements (listed entity has flexibility regarding the placement of this disclosure)
Details of the highest authority responsible for implementation and oversight of the Business Responsibility policy (ies).
Does the entity have a specified Committee of the Board/ Director responsible for decision making on sustainability related issues? (Yes / No). If yes, provide details.
Indicate whether review was undertaken by Director / Committee of the Board/ Any other Committee
Frequency(Annually/ Half yearly/ Quarterly/ Any other – please specify)
Has the entity carried out independent assessment/ evaluation of the working of its policies by an external agency? (Yes/No). If yes, provide name of the agency.
If answer to question (1) above is “No” i.e. not all Principles are covered by a policy, reasons to be stated, as below:
Upstream (Suppliers & Logistics Partners)
Downstream (Distributors & Customers)
"""

def extract_json_from_text(text):
    brace_stack = []
    start_index = None
    for i, char in enumerate(text):
        if char == '{':
            if start_index is None:
                start_index = i
            brace_stack.append('{')
        elif char == '}':
            if brace_stack:
                brace_stack.pop()
                if not brace_stack:
                    json_str = text[start_index:i + 1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
    return None

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def chunk_text(text,max_tokens=1500):
    paragraphs = text.split("\n" )
    chunks, current_chunk = [], ""
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_tokens:
            current_chunk += para + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = para + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def extract_fields_with_gemini(text_chunk: str) -> dict:
    model = genai.GenerativeModel("gemini-2.0-flash" )
    prompt = f"""
You are an expert in information extraction. Extract the following details from the provided text and return them in valid JSON format with keys exactly as listed below. Only return the JSON — no extra commentary.

{KEYS_TO_EXTRACT}

TEXT:
{text_chunk}
"""
    try:
        response = model.generate_content(prompt)
        parsed = extract_json_from_text(response.text)
        return parsed if parsed else {}
    except ResourceExhausted:
        raise HTTPException(status_code=429, detail="Gemini API quota exceeded." )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def merge_results(results):
    final = {}
    for result in results:
        for k, v in result.items():
            if k not in final or not final[k]:
                final[k] = v
    return final


    
def parse_brsr_text(json_merge):
    return {
    "data": [
      {
        "title": "GENERAL DISCLOSURES",
        "section": "section_a",
        "parts": [
          {
            "partNo": "one",
            "subtitle": "Details of the listed entity",
            "questions": [
              {
                "questionNo": "1",
                "question": "Corporate Identity Number (CIN) of the Listed Entity",
                "questionOptions": [],
                "questionAnswer": json_merge["Corporate Identity Number (CIN) of the Listed Entity"]
              },
              {
                "questionNo": "2",
                "question": "Name of the Listed Entity",
                "questionOptions": [],
                "questionAnswer": json_merge["Name of the Listed Entity"]
              },
              {
                "questionNo": "3",
                "question": "Year of incorporation",
                "questionOptions": [],
                "questionAnswer": json_merge["Year of incorporation"]
              },
              {
                "questionNo": "4",
                "question": "Registered office address",
                "questionOptions": [],
                "questionAnswer": json_merge["Registered office address"]
              },
              {
                "questionNo": "5",
                "question": "Corporate address",
                "questionOptions": [],
                "questionAnswer": json_merge["Corporate address"]
              },
              {
                "questionNo": "6",
                "question": "Email",
                "questionOptions": [],
                "questionAnswer": json_merge["Email"]
              },
              {
                "questionNo": "7",
                "question": "Telephone",
                "questionOptions": [],
                "questionAnswer": json_merge["Telephone"]
              },
              {
                "questionNo": "8",
                "question": "Website",
                "questionOptions": [],
                "questionAnswer": json_merge["Website"]
              },
              {
                "questionNo": "9",
                "question": "Financial year for which reporting is being done",
                "questionOptions": [],
                "questionAnswer": json_merge["Financial year for which reporting is being done"]
              },
              {
                "questionNo": "10",
                "question": "Name of the Stock Exchange(s) where shares are listed",
                "questionOptions": [],
                "questionAnswer": json_merge["Name of the Stock Exchange(s) where shares are listed"]
              },
              {
                "questionNo": "11",
                "question": "Paid-up Capital",
                "questionOptions": [],
                "questionAnswer": json_merge["Paid-up Capital"]
              },
              {
                "questionNo": "12",
                "question": "Name and contact details of the person who may be contacted",
                "questionOptions": [],
                "questionAnswer": json_merge["Name and contact details"]
              },
              {
                "questionNo": "13",
                "question": "Reporting boundary - Are the disclosures under this report made on a standalone basis (i.e. only for the entity) or on a consolidated basis (i.e. for the entity and all the entities which form a part of its consolidated financial statements, taken together)",
                "questionOptions": [],
                "questionAnswer": json_merge["Reporting boundary - Are the disclosures under this report made on a standalone basis (i.e. only for the entity) or on a consolidated basis (i.e. for the entity and all the entities which form a part of its consolidated financial statements, taken together)"]
              },
              {
                "questionNo": "14",
                "question": "Name of assurance provider",
                "questionOptions": [],
                "questionAnswer": json_merge["Name of assurance provider"]
              },
              {
                "questionNo": "15",
                "question": "Type of assurance obtained",
                "questionOptions": [],
                "questionAnswer": json_merge["Type of assurance obtained"]
              }
            ]
          },
          {
            "partNo": "two",
            "subtitle": "Products / Services",
            "questions": [
              {
                "questionNo": "1",
                "question": "Details of business activities (accounting for 90% of the turnover)",
                "questionOptions": [],
                "questionAnswer": json_merge["Details of business activities (accounting for 90% of the turnover)"]
              },
              {
                "questionNo": "2",
                "question": "Products/Services sold by the entity (accounting for 90% of the entity’s Turnover):",
                "questionOptions": [],
                "questionAnswer": json_merge["Products/Services sold by the entity (accounting for 90% of the entity’s Turnover):"]
              }
            ]
          },
          {
            "partNo": "three",
            "subtitle": "Operations",
            "questions": [
              {
                "questionNo": "1",
                "question": "No. of locations where plants and/or operations/ offices of the entity are situated:",
                "questionOptions": [],
                "questionAnswer": json_merge["No. of locations where plants and/or operations/ offices of the entity are situated:"]
              },
              {
                "questionNo": "2",
                "question": "Markets served by the entity",
                "questionOptions": [
                  {
                    "option": "a",
                    "questionAnswer": json_merge["No. of Locations"]
                  },
                  {
                    "option": "b",
                    "questionAnswer": json_merge["What is the contribution of exports as a percentage of the total turnover of the entity?"]
                  }
                ],
                "questionAnswer": ""
              }
            ]
          },
          {
            "partNo": "four",
            "subtitle": "Employees",
            "questions": [
              {
                "questionNo": "1",
                "question": "Details as at the end of Financial Year",
                "questionOptions": [
                  {
                    "option": "a",
                    "questionAnswer": json_merge["Employees and workers (including differently abled):"]
                  },
                  {
                    "option": "b",
                    "questionAnswer": json_merge["Differently abled Employees and workers:"]
                  }
                ],
                "questionAnswer": ""
              },
              {
                "questionNo": "2",
                "question": "Participation/Inclusion/Representation of women",
                "questionOptions": [],
                "questionAnswer": json_merge["Participation/Inclusion/Representation of women"]
              },
              {
                "questionNo": "3",
                "question": "Turnover rate for permanent employees and workers (Disclose trends for the past 3 years)",
                "questionOptions": [],
                "questionAnswer": json_merge["Turnover rate for permanent employees and workers (Disclose trends for the past 3 years)"]
              }
            ]
          },
          {
            "partNo": "five",
            "subtitle": "Holding, Subsidiary and Associate Companies (including joint ventures)",
            "questions": [
              {
                "questionNo": "1",
                "question": "How many products have undergone a carbon footprint assessment?",
                "questionOptions": [],
                "questionAnswer": json_merge["How many products have undergone a carbon footprint assessment?"]
              }
            ]
          },
          {
            "partNo": "six",
            "subtitle": "CSR Details",
            "questions": [
              {
                "questionNo": "1",
                "question": "CSR_details",
                "questionOptions": [
                  {
                    "option": "a",
                    "questionAnswer": json_merge["Whether CSR is applicable as per section 135 of Companies Act, 2013: (Yes/No)"]
                  },
                  {
                    "option": "b",
                    "questionAnswer": json_merge["Turnover (in Rs.)"]
                  },
                  {
                    "option": "c",
                    "questionAnswer": json_merge["Net worth (in Rs.)"]
                  }
                ],
                "questionAnswer": ""
              }
            ]
          },
          {
            "partNo": "seven",
            "subtitle": "Transparency and Disclosures Compliances",
            "questions": [
              {
                "questionNo": "1",
                "question": "Complaints/Grievances on any of the principles (Principles 1 to 9) under the National Guidelines on Responsible Business Conduct:",
                "questionOptions": [],
                "questionAnswer": json_merge["Complaints/Grievances on any of the principles (Principles 1 to 9) under the National Guidelines on Responsible Business Conduct:"]
              },
              {
                "questionNo": "2",
                "question": "Overview of the entity’s material responsible business conduct issues",
                "questionOptions": [
                  {
                    "option": "a",
                    "questionAnswer": json_merge["Please indicate material responsible business conduct and sustainability issues pertaining to environmental and social matters that present a risk or an opportunity to your business, rationale for identifying the same, approach to adapt or mitigate the risk along-with its financial implications, as per the following format."]
                  }
                ],
                "questionAnswer": ""
              }
            ]
          }
        ]
      },
    {
        "title": "MANAGEMENT AND PROCESS DISCLOSURES",
        "section": "section_b",
        "parts": [
          {
            "partNo": "one",
            "subtitle": "Policy and management processes",
            "questions": [
              {
                "questionNo": "1",
                "question": "Whether your entity’s policy/policies cover each principle and its core elements of the NGRBCs. (Yes/No) (Yes/No)",
                "questionOptions": [],
                "questionAnswer": json_merge["Whether your entity’s policy/policies cover each principle and its core elements of the NGRBCs. (Yes/No)"]
              }
            ]
          },
          {
            "partNo":"two",
            "subtitle": "Governance, leadership and oversight",
            "questions": [
              {
                "questionNo": "1",
                "question": "Statement by director responsible for the business responsibility report, highlighting ESG related challenges, targets and achievements (listed entity has flexibility regarding the placement of this disclosure)",
                "questionOptions": [],
                "questionAnswer": json_merge["Statement by director responsible for the business responsibility report, highlighting ESG related challenges, targets and achievements (listed entity has flexibility regarding the placement of this disclosure)"]
              },
              {
                "questionNo": "2",
                "question": "Details of the highest authority responsible for implementation and oversight of the Business Responsibility policy (ies).",
                "questionOptions": [],
                "questionAnswer": json_merge["Details of the highest authority responsible for implementation and oversight of the Business Responsibility policy (ies)."]
              },
              {
                "questionNo": "3",
                "question": "Does the entity have a specified Committee of the Board/ Director responsible for decision making on sustainability related issues? (Yes / No). If yes, provide details.",
                "questionOptions": [],
                "questionAnswer": json_merge["Does the entity have a specified Committee of the Board/ Director responsible for decision making on sustainability related issues? (Yes / No). If yes, provide details."]
              },
              {
                "questionNo": "4",
                "question": "Details of Review of NGRBCs by the Company:",
                "questionOptions": [
                {
                    "option": "a",
                    "questionAnswer": json_merge["Indicate whether review was undertaken by Director / Committee of the Board/ Any other Committee"]
                  },
                  {
                    "option": "b",
                    "questionAnswer": json_merge["Frequency(Annually/ Half yearly/ Quarterly/ Any other – please specify)"]
                  }
                ],
                "questionAnswer":"",
              },
              {
                "questionNo": "5",
                "question": "Has the entity carried out independent assessment/ evaluation of the working of its policies by an external agency? (Yes/No). If yes, provide name of the agency.",
                "questionOptions": [],
                "questionAnswer": json_merge["Has the entity carried out independent assessment/ evaluation of the working of its policies by an external agency? (Yes/No). If yes, provide name of the agency."]
              },
              {
                "questionNo": "6",
                "question": "If answer to question (1) above is “No” i.e. not all Principles are covered by a policy, reasons to be stated, as below:",
                "questionOptions": [],
                "questionAnswer": json_merge["If answer to question (1) above is “No” i.e. not all Principles are covered by a policy, reasons to be stated, as below:"]
              },
              {
                "questionNo": "7",
                "question": "Supply Chain Management",
                "questionOptions": [
                                    {
                    "option": "a",
                    "questionAnswer": json_merge["Upstream (Suppliers & Logistics Partners)"]
                  },
                  {
                    "option": "b",
                    "questionAnswer": json_merge["Downstream (Distributors & Customers)"]
                  }
                    
                    ],
              },
            ]
          }
        ]
      },
    
    
    ]
  }
@app.post("/hu")
def postmy(name:str):
    
    return {"my Name is":name}

@app.get("/k")
def suman():
    return {"message":"suman"}


@app.post("/extract/" )
async def extract_document(file: UploadFile = File(...)):
    if not (file.filename.endswith(".pdf" ) or file.filename.endswith(".docx" )):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported." )
    
    content = await file.read()
    temp_path = f"temp_{file.filename}"
    
    with open(temp_path, "wb" ) as f:
        f.write(content)

    try:
        if file.filename.endswith(".pdf" ):
            text = extract_text_from_pdf(temp_path)
        else:
            text = extract_text_from_docx(temp_path)
        
        chunks = chunk_text(text)
        results = [extract_fields_with_gemini(chunk) for chunk in chunks[:5]]
        print(results)
        merged = merge_results(results)
        res=parse_brsr_text(merged)
        return res

        
        
        # return JSONResponse(content=merged)
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="debug" )
