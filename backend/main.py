import base64,hashlib,json,logging,os,re,wave
from pathlib import Path
from typing import Any,Literal
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel,Field
ROOT=Path(__file__).resolve().parent;load_dotenv(ROOT/'.env');CACHE=ROOT/'audio-cache';CACHE.mkdir(exist_ok=True);LOCAL_UPDATES=ROOT/'local_updates.json';YEAR_DATA=ROOT/'year_data.json'
logger=logging.getLogger('floodlens')
def safe_provider_message(exc:Exception)->str:
 message=str(exc)
 key=os.getenv('GEMINI_API_KEY')
 if key:message=message.replace(key,'[REDACTED]')
 message=re.sub(r'(?i)(authorization|x-goog-api-key|api[_-]?key)(["\'\s:=]+)[^,\s}\]]+',r'\1\2[REDACTED]',message)
 return message[:600]
app=FastAPI(title='TerraNexis FloodLens Myanmar API',version='0.1.0');app.add_middleware(CORSMiddleware,allow_origins=[os.getenv('FRONTEND_ORIGIN','http://localhost:5173')],allow_methods=['*'],allow_headers=['*'])
class ExplanationRequest(BaseModel): result:dict[str,Any];language:Literal['en','my']='en'
class TTSRequest(BaseModel): text:str=Field(min_length=1,max_length=8000);voice:str|None=None;language:Literal['en','my']='en'
def fallback(result:dict[str,Any],lang:str)->str:
 s=result.get('settlement',{}).get('name','the selected location');d=result.get('dates',{})
 if lang=='my':return f'{s} အတွက် {d.get("before","")} မှ {d.get("after","")} အထိ ပြင်ဆင်ထားသော ရလဒ်များတွင် ဖြစ်နိုင်သည့် ထိတွေ့မှုကို ဖော်ပြထားသည်။ ဤသည်မှာ တိုက်ရိုက်လက်ရှိ ရေကြီးမှုအချက်အလက်မဟုတ်ပါ။ လမ်းနှင့်ပတ်သက်သည့် အလံများကို ဒေသခံအတည်ပြုမှု လိုအပ်သော အချက်အလက်အဖြစ်သာ သတ်မှတ်ပါ။'
 if lang=='my':return f'{s} အတွက် {d.get("before","")} မှ {d.get("after","")} အထိ နမူနာအချက်အလက်အရ ထိစပ်နိုင်မှုရှိပါသည်။ ဤသည်မှာ တိုက်ရိုက်ရေဘေးအချက်အလက် မဟုတ်ပါ။ လမ်းအမှတ်အသားများကို ဒေသတွင်းစစ်ဆေးရန် လိုအပ်ပါသည်။'
 return f'For {s}, the comparison from {d.get("before","")} to {d.get("after","")} shows potential overlap in prepared results. This is illustrative demo data, not live flood information. Treat any road flag as requiring local verification.'
@app.get('/api/health')
def health():return {'ok':True,'demoData':True,'geminiConfigured':bool(os.getenv('GEMINI_API_KEY'))}
def load_local_updates()->list[dict[str,Any]]:
 try:
  payload=json.loads(LOCAL_UPDATES.read_text(encoding='utf-8'))
  return payload.get('incidents',[]) if isinstance(payload,dict) and isinstance(payload.get('incidents',[]),list) else []
 except (OSError,json.JSONDecodeError) as e:
  logger.error('Local updates feed could not be loaded: %s',type(e).__name__)
  return []
def public_incident(item:dict[str,Any])->dict[str,Any]:
 return {
  'id':item.get('id',''),'type':item.get('type','flood'),'region':item.get('region',''),'township':item.get('township',''),
  'locationScope':item.get('location_scope','township'),'locationLabel':item.get('location_label'),
  'title':item.get('title',{'en':'','my':''}),'summary':item.get('summary',{'en':'','my':''}),
  'eventDate':item.get('event_date'),'publicationDate':item.get('publication_date',''),'lastUpdated':item.get('last_updated',''),
  'sourceName':item.get('source_name',''),'sourceUrl':item.get('source_url',''),'verificationStatus':item.get('verification_status','pending'),
  'coordinates':item.get('coordinates') if item.get('verification_status')=='verified' else None,'sourcedAdvice':item.get('sourced_advice')
 }
@app.get('/api/local-updates')
def local_updates(region:str|None=None,township:str|None=None):
 region_key=(region or '').strip().casefold();township_key=(township or '').strip().casefold();incidents=[]
 for item in load_local_updates():
  if not isinstance(item,dict):continue
  if region_key and str(item.get('region','')).casefold()!=region_key:continue
  if township_key and township_key not in str(item.get('township','')).casefold() and township_key not in str(item.get('location_label','')).casefold():continue
  incidents.append(public_incident(item))
 return {'incidents':incidents,'available':bool(incidents),'region':region or None,'township':township or None}
@app.get('/api/year-data')
def year_data(year:int,region:str|None=None):
 try:
  payload=json.loads(YEAR_DATA.read_text(encoding='utf-8'));record=payload.get('years',{}).get(str(year))
 except (OSError,json.JSONDecodeError) as e:
  logger.error('Year data feed could not be loaded: %s',type(e).__name__);record=None
 if not isinstance(record,dict):record={'available':False,'before':None,'after':None,'source_label':'No year-specific dataset loaded','observation_note':'Analysis pending; no source-backed observation window is available.'}
 return {'year':year,'available':bool(record.get('available',False)),'before':record.get('before'),'after':record.get('after'),'sourceLabel':record.get('source_label',''),'observationNote':record.get('observation_note',''),'region':region or None}
@app.post('/api/explanation')
def explanation(req:ExplanationRequest):
 f=fallback(req.result,req.language);key=os.getenv('GEMINI_API_KEY')
 if not key:return {'text':f,'fallback':True,'reason':'GEMINI_API_KEY is not configured'}
 try:
  from google import genai
  c=genai.Client(api_key=key);prompt='Return only a concise explanation grounded strictly in this structured analysis JSON. Preserve dates and uncertainty. Do not forecast, give evacuation instructions, or recommend safe routes. '+json.dumps({'result':req.result,'language':req.language},ensure_ascii=False)
  x=c.models.generate_content(model=os.getenv('GEMINI_EXPLANATION_MODEL','gemini-3.1-flash-lite'),contents=prompt);t=(x.text or '').strip()
  return {'text':t or f,'fallback':not bool(t),'reason':None if t else 'Empty Gemini response'}
 except Exception as e:return {'text':f,'fallback':True,'reason':'Gemini unavailable: '+type(e).__name__}
@app.post('/api/tts')
def tts(req:TTSRequest):
 key=os.getenv('GEMINI_API_KEY')
 if not key:raise HTTPException(503,'TTS unavailable: GEMINI_API_KEY is not configured.')
 model=os.getenv('GEMINI_TTS_MODEL','gemini-3.8-flash-tts');voice=req.voice or os.getenv('GEMINI_TTS_VOICE','Kore');h=hashlib.sha256((req.language+'\\0'+req.text+'\\0'+model+'\\0'+voice).encode()).hexdigest();p=CACHE/(h+'.wav')
 if p.exists():return Response(p.read_bytes(),media_type='audio/wav',headers={'X-TTS-Cache':'HIT'})
 try:
  from google import genai
  from google.genai import types
  c=genai.Client(api_key=key)
  config=types.GenerateContentConfig(
   response_modalities=['AUDIO'],
   speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(voice=voice)),
  )
  contents=types.Content(role='user',parts=[types.Part(text=req.text,speech_metadata=types.SpeechMetadata(style='clear, calm public information readout'))])
  x=c.models.generate_content(model=model,contents=[contents],config=config)
  part=x.candidates[0].content.parts[0] if x.candidates and x.candidates[0].content and x.candidates[0].content.parts else None
  inline=getattr(part,'inline_data',None) if part else None
  raw=getattr(inline,'data',None) if inline else None
  if isinstance(raw,str):raw=base64.b64decode(raw)
  if not raw:raise ValueError('empty audio response')
  mime=(getattr(inline,'mime_type','') or '').lower()
  if 'wav' in mime or raw[:4]==b'RIFF':data=raw
  else:
   import io
   out=io.BytesIO()
   with wave.open(out,'wb') as wf:
    wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(24000);wf.writeframes(raw)
   data=out.getvalue()
  if data[:4]!=b'RIFF':raise ValueError('audio response was not WAV data')
  p.write_bytes(data);return Response(data,media_type='audio/wav',headers={'X-TTS-Cache':'MISS'})
 except ImportError:
  logger.error('TTS dependency missing')
  raise HTTPException(503,'TTS is not installed on the backend. Run: py -m pip install -r requirements.txt')
 except Exception as e:
  status=getattr(e,'status_code',None) or getattr(getattr(e,'response',None),'status_code',None)
  code=getattr(e,'code',None)
  safe=safe_provider_message(e);logger.error('TTS provider request failed: type=%s status=%s code=%s message=%s',type(e).__name__,status,code,safe)
  name=type(e).__name__.lower();message=(str(status)+' '+str(code)+' '+safe).lower()
  if 'connect' in name or 'timeout' in name or 'connection' in name or 'network' in message:detail='TTS provider could not be reached from the backend. Check network/proxy access to the Gemini API and try again.'
  elif status==429 or '429' in message or 'quota' in message or 'rate' in message:detail='TTS provider quota or rate limit reached. Check the Gemini project quota and try again later.'
  elif status in (401,403) or '401' in message or '403' in message or 'permission' in message or 'api key' in message or 'authentication' in message:detail='TTS provider authentication or permission failed. Check the configured Gemini API key and project access.'
  elif 'user location is not supported' in message or 'location is not supported' in message:detail='TTS is unavailable because the Gemini API does not support the backend user location. Use a supported deployment region or configure another TTS provider.';status=503
  elif status==404 or '404' in message or 'not found' in message or 'model' in message or 'voice' in message:detail='TTS configuration was rejected. Check the configured Gemini TTS model and voice.'
  elif str(status).isdigit() and int(status)>=500:detail='The Gemini TTS provider is temporarily unavailable. Try again later.'
  else:detail='TTS provider returned no playable audio. Check the configured Gemini TTS model and voice.'
  raise HTTPException(503 if status==503 else 502,detail)
