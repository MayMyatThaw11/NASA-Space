import type{Result,Settlement}from'./types';

const cleanBurmeseExplanation='ရွေးချယ်ထားသောနေရာအတွက် ပြင်ဆင်ထားသော နှိုင်းယှဉ်လေ့လာချက်ကို ပြသထားသည်။ ဤသည်မှာ တိုက်ရိုက်လက်ရှိ ရေကြီးမှုအကဲဖြတ်ချက် မဟုတ်ပါ။ လမ်းအလံများသည် ဒေသခံအတည်ပြုမှု လိုအပ်သည်။';

export const regions=['Rakhine','Tanintharyi','Ayeyarwady'] as const;

export const places:Settlement[]=[
  {id:'sittwe',name:'Sittwe',nameMm:'စစ်တွေ',region:'Rakhine',type:'city',coordinates:[20.15,92.9]},
  {id:'sittwe-waterfront',name:'Sittwe Waterfront',nameMm:'စစ်တွေကမ်းနားရပ်ကွက်',region:'Rakhine',type:'neighborhood',coordinates:[20.145,92.905]},
  {id:'mrauk-u',name:'Mrauk-U',nameMm:'မြောက်ဦး',region:'Rakhine',type:'town',coordinates:[20.6,93.19]},
  {id:'kyaukphyu-village',name:'Kyaukphyu Delta',nameMm:'ကျောက်ဖြူကျေးရွာ',region:'Rakhine',type:'village',coordinates:[19.42,93.55]},
  {id:'dawei',name:'Dawei',nameMm:'ထားဝယ်',region:'Tanintharyi',type:'city',coordinates:[14.08,98.2]},
  {id:'myeik',name:'Myeik',nameMm:'မြိတ်',region:'Tanintharyi',type:'town',coordinates:[12.44,98.6]},
  {id:'kawthaung',name:'Kawthaung',nameMm:'ကော့သောင်း',region:'Tanintharyi',type:'town',coordinates:[9.98,98.55]},
  {id:'dawei-river',name:'Dawei River Quarter',nameMm:'ထားဝယ်မြစ်ကမ်းရပ်ကွက်',region:'Tanintharyi',type:'neighborhood',coordinates:[14.09,98.19]},
  {id:'pathein',name:'Pathein',nameMm:'ပုသိမ်',region:'Ayeyarwady',type:'city',coordinates:[16.78,94.73]},
  {id:'labutta',name:'Labutta',nameMm:'လပွတ္တာ',region:'Ayeyarwady',type:'town',coordinates:[16.13,94.1]},
  {id:'hinthada-village',name:'Hinthada South',nameMm:'ဟင်္သာတတောင်ပိုင်းကျေးရွာ',region:'Ayeyarwady',type:'village',coordinates:[17.65,95.46]},
  {id:'pathein-market',name:'Pathein Riverside',nameMm:'ပုသိမ်မြစ်ကမ်းရပ်ကွက်',region:'Ayeyarwady',type:'neighborhood',coordinates:[16.775,94.735]},
];

const burmese='ဤနေရာအတွက် ပြသထားသော ရလဒ်သည် နမူနာဒေတာသာ ဖြစ်ပါသည်။ ပြောင်းလဲမှုအလွှာနှင့် လမ်းညွှန်အချက်များကို ဒေသတွင်းအတည်ပြုချက် မရမချင်း အတည်ပြုထားသော ရေလွှမ်းမိုးမှု သို့မဟုတ် လမ်းပိတ်မှုအဖြစ် မယူဆပါနှင့်။';

export const results:Result[]=places.map((settlement,index)=>{
  const pending=settlement.id==='labutta';
  const exposed=pending?0:Math.max(1,(index%4)+1);
  const total=pending?0:12+(index%3)*4;
  const flagged=pending?0:Number((1.2+(index%4)*0.7).toFixed(1));
  const roadName=settlement.region==='Rakhine'?'Sittwe–Pauktaw connector':settlement.region==='Tanintharyi'?'Regional coastal connector':'Delta access road';
  return{
    settlement,
    dates:{before:'2024-08-10',after:'2024-08-22'},
    exposure:{settlement:{exposed,total,status:pending?'missing':'potential'},road:{flaggedKm:flagged,status:pending?'missing':'potential'}},
    uncertainty:['Geometry and statistics require local validation.','Cloud, tide, and classification uncertainty are not quantified.'],
    missingData:pending?['Settlement footprint processing is pending for this location.']:[],
    roads:pending?[]:[{name:roadName,reason:'Potential intersection with the prepared change layer.',evidence:'Prepared geometry only; requires local verification.'}],
    explanation:{
      en:`${settlement.name} has a prepared comparison layer for the selected window. This is not a live flood assessment. Any road flag requires local verification.`,
      my:cleanBurmeseExplanation,
    },
    analysisStatus:pending?'pending':'ready',
    sourceLabel:'Prepared comparison layer',
    coverage:pending?'Analysis pending':'Priority region · prepared geometry',
    observationNote:'Comparison window; not a confirmed acquisition record.',
  };
});
