const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface FullAnalysisResult {
  resume: {
    candidate_summary: string;
    skills: string[];
    education: string[];
    experience: string[];
    projects: string[];
  };
  role: {
    role_title: string;
    required_skills: string[];
    keywords: string[];
    typical_responsibilities: string[];
  };
  matched_skills: string[];
  missing_skills: string[];
  match_percentage: number;
  match_analysis: string;
  suggestions: { missing_skill: string; suggestion: string }[];
  overall_advice: string;
}

export async function analyzeResume(file: File, roleTitle: string): Promise<FullAnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("role_title", roleTitle);

  const response = await fetch(`${API_URL}/full-analysis`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}