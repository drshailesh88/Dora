// API Response Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  specialty?: string;
  institution?: string;
  is_verified: boolean;
  email_verified: boolean;
  mfa_enabled: boolean;
  license_tier: string;
  avatar_url?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role?: string;
  specialty?: string;
  institution?: string;
  registration_number?: string;
}

export interface MedicalQuery {
  question: string;
  patient_id?: number;
  patient_context?: PatientContext;
  top_k?: number;
  use_multi_query?: boolean;
  use_hyde?: boolean;
}

export interface PatientContext {
  age?: number;
  gender?: string;
  conditions?: string[];
  medications?: string[];
  allergies?: string[];
}

export interface Citation {
  text: string;
  source: string;
  page?: number;
  score: number;
}

export interface MedicalAnswer {
  answer: string;
  citations: Citation[];
  confidence_score: number;
  retrieved_chunks: number;
  query_time_ms: number;
  warnings: string[];
}

export interface QueryResponse {
  success: boolean;
  answer?: MedicalAnswer;
  error?: string;
}

export interface DrugInteraction {
  drug1: string;
  drug2: string;
  severity: "minor" | "moderate" | "major" | "contraindicated";
  description: string;
  management: string;
  source: string;
}

export interface DrugInteractionResponse {
  success: boolean;
  interactions: DrugInteraction[];
  warnings: string[];
  error?: string;
}

export interface LicenseStatus {
  status: string;
  tier?: string;
  message: string;
  features: string[];
  daily_limit: number;
  expires_at?: string;
}

export interface PaymentOrder {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}
