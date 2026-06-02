export interface FieldMapping {
  term_field: string;
  translation_field?: string | null;
  context_field?: string | null;
  context_trans_field?: string | null;
  lemma_field?: string | null;
  part_of_speech_field?: string | null;
  image_field?: string | null;
  audio_field?: string | null;
}

export interface DetectedFieldInfo {
  name: string;
  sample: string;
  has_image: boolean;
  has_audio: boolean;
}

export interface AnkiPreviewResponse {
  import_token: string;
  deck_name: string;
  card_count: number;
  media_size_bytes: number;
  detected_fields: DetectedFieldInfo[];
  suggested_mapping: FieldMapping;
}

export interface AnkiConfirmRequest {
  import_token: string;
  source_lang_id: number;
  target_lang_id: number;
  title?: string;
  field_mapping: FieldMapping;
}

export interface AnkiImportResponse {
  set_id: number;
  title: string;
  item_count: number;
  skipped_count: number;
  reused_count: number;
  no_gap_count: number;
}

export interface LpsetImportResponse {
  set_id: number;
  title: string;
  item_count: number;
  skipped_count: number;
  reused_count: number;
}
