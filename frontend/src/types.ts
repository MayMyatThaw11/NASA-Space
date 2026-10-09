export type SettlementType='village'|'town'|'city'|'neighborhood';
export type AnalysisStatus='ready'|'pending';

export interface Settlement{
  id:string;
  name:string;
  nameMm:string;
  region:string;
  type:SettlementType;
  coordinates:[number,number];
}

export interface Result{
  settlement:Settlement;
  dates:{before:string;after:string};
  exposure:{settlement:{exposed:number;total:number;status:string};road:{flaggedKm:number;status:string}};
  uncertainty:string[];
  missingData:string[];
  roads:{name:string;reason:string;evidence:string}[];
  explanation:{en:string;my:string};
  analysisStatus:AnalysisStatus;
  sourceLabel:string;
  coverage:string;
  observationNote:string;
}

export type IncidentType='flood'|'landslide';
export type VerificationStatus='verified'|'unverified'|'pending';
export type IncidentScope='township'|'neighborhood';

export interface Incident{
  id:string;
  type:IncidentType;
  region:string;
  township:string;
  locationScope:IncidentScope;
  locationLabel?:string;
  title:{en:string;my:string};
  summary:{en:string;my:string};
  eventDate:string|null;
  publicationDate:string;
  lastUpdated:string;
  sourceName:string;
  sourceUrl:string;
  verificationStatus:VerificationStatus;
  coordinates:[number,number]|null;
  sourcedAdvice:{en:string;my:string}|null;
}

export interface YearAnalysis{
  year:number;
  available:boolean;
  before:string|null;
  after:string|null;
  sourceLabel:string;
  observationNote:string;
}
