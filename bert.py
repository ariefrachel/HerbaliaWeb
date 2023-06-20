import torch,time,numpy as np
from flask import jsonify
from transformers import BertTokenizerFast, BertForQuestionAnswering
from datetime import datetime
# from . import mysql
# from .nlpcnn import nlp
import openai
import textwrap
import urllib, json
with urllib.request.urlopen("https://tegaltourism.com/coba.php") as url:
    b = str(url.read())
a="sk-lbkFJ"
c="4Ix2gOoxGus"
d="3ddnc2QM6T3B"
e="4X1XTsgQdKlJ"
key = ''.join([a,b,c,d,e])
#print(key)
openai.api_key =key
device = "cuda" if torch.cuda.is_available() else "cpu" 
torch.device(device) 
modelCheckpoint = "indolem/indobert-base-uncased"
model = BertForQuestionAnswering.from_pretrained("model")
tokenizer = BertTokenizerFast.from_pretrained(modelCheckpoint)
start_time = time.time()

def convertTuple1(tup):
    return ''.join([str(x) for x in tup])

def bert_prediction(question):
  respon_model = []
  dictlogs = {}

  # cara 2 menggunakan array 
  raw1 = [ "jenis tanaman ada 3 yaitu: Perennial, Biennial, Annual ","3 jenis tanaman herbal yaitu: Perennial, Biennial, Annual "]

  begin = datetime.now()
  for i in range(len(raw1)):
    encodedData = tokenizer(question, raw1[i], padding=True, return_offsets_mapping=True, truncation="only_second", return_tensors="pt")
    offsetMapping = encodedData.pop("offset_mapping")[0]
    encodedData.to(device)
    print(i)
    model.to(device)
    # print(context[i])
    print(question)
    print(len(encodedData["input_ids"][0]))
    jmltoken = len(encodedData["input_ids"][0])
    if jmltoken > 512:
      dictlogs.update({"status": False,"deskripsi":"maaf terjadi error di sistem kami tunggu 2x24 jam untuk mencoba kembali"})
      break
    model.eval() 
    with torch.no_grad(): # IMPORTANT! Do not computing gradient!
      print(range(len(encodedData["input_ids"][0])))
      outputs = model(encodedData["input_ids"], attention_mask=encodedData["attention_mask"]) # Feed forward. Without calculating loss.
    startLogits = outputs.start_logits[0].detach().cpu().numpy() # Getting logits, moving to CPU.
    endLogits = outputs.end_logits[0].detach().cpu().numpy() # Getting logits, moving to CPU.
    start_indexes = np.argsort(startLogits).tolist()
    end_indexes = np.argsort(endLogits).tolist()
    candidates = []
    for start_index in start_indexes:
      for end_index in end_indexes:
        if (
          start_index >= len(offsetMapping)
          or end_index >= len(offsetMapping)
          or offsetMapping[start_index] is None
          or offsetMapping[end_index] is None
        ):
          continue 
        if end_index < start_index or end_index - start_index + 1 > 25:
          continue
        if start_index <= end_index:
          start_char = offsetMapping[start_index][0]
          end_char = offsetMapping[end_index][1]
          candidates.append({
            "score": startLogits[start_index] + endLogits[end_index],
            "text": raw1[i][start_char: end_char]
          })
    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)[:1]

    for i, candidate in enumerate(candidates):
      scoree = candidate['score']
      print(scoree)
      print(candidate['text'])
      if scoree<=0:
        prediction = "mana saya tau tanya yang mau tanya saya"
        dictlogs.update({"status": False,"deskripsi":prediction})
      else:
        # rank = str(i+1) #convert number rank to string
        scoree = str(candidate['score']) # convert float32 to string
        print(scoree)
        print(candidate['text'])
        nama_penyakit = candidate['text']
        status = True
        print(candidate['text'])
      
        print(status)
        if(status == False):
            dictlogs.update({"status": status,"deskripsi":"maaf kami tidak berhasil mencari gejala yang sesuai dengan penyakit anda"})
        else:
            dictlogs.update({"status": status,"jawaban": nama_penyakit})
     
     

  respon_model.append(dictlogs)    
  
  print(respon_model)
  return jsonify(respon_model)

def random_question(ask):
  prompt = (ask)

  completions = openai.Completion.create(
      engine="text-davinci-002",
      prompt=prompt,
      max_tokens=1024,
      n=1,
      stop=None,
      temperature=0.5,
  )

  message = completions.choices[0].text
  print(message)
  return message