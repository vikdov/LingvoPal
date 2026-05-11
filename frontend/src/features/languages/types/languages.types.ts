export interface LanguageRef {
  id: number;
  code: string;
  name: string;
}

export interface UserLanguage {
  language: LanguageRef;
  is_active: boolean;
  created_at: string;
}

export interface UserLanguagesResponse {
  languages: UserLanguage[];
  active_language: LanguageRef | null;
}

export interface AddUserLanguageRequest {
  language_id: number;
  set_active?: boolean;
}
