# 12 — High-Level Data Model and ERD

Conventions: every tenant-owned table has `tenant_id` (RLS), `id` (UUIDv7), `created_at`, `updated_at`, `created_by`; soft delete only where the domain needs it (people), hard delete elsewhere with audit. `ayah_index` is the global Ayah sequence within a Riwayah from the Quran Core. Diagrams are split by domain; cross-domain references are noted in text.

## 12.1 Identity, tenancy, permissions

```mermaid
erDiagram
  ACCOUNT ||--o{ MEMBERSHIP : has
  TENANT ||--o{ MEMBERSHIP : includes
  MEMBERSHIP ||--o{ ROLE_ASSIGNMENT : holds
  ROLE ||--o{ ROLE_ASSIGNMENT : granted_by
  ROLE ||--o{ ROLE_PERMISSION : grants
  TENANT ||--o{ ROLE : defines
  ACCOUNT ||--o{ SESSION_TOKEN : owns
  ACCOUNT ||--o{ MFA_FACTOR : owns
  ACCOUNT ||--o{ DEVICE : registers
  TENANT ||--o{ BRANCH : has
  TENANT ||--o{ TENANT_MODULE : enables
  TENANT ||--o{ TENANT_FEATURE_FLAG : sets
  BRANCH ||--o{ BRANCH_MODULE_OVERRIDE : restricts
  TENANT ||--o{ API_KEY : issues
  TENANT ||--o{ WEBHOOK_SUBSCRIPTION : registers

  ACCOUNT { uuid id PK  citext email  string phone  string password_hash  string status  string locale  timestamptz last_login_at }
  MEMBERSHIP { uuid id PK  uuid account_id FK  uuid tenant_id FK  uuid person_id FK  string status }
  ROLE_ASSIGNMENT { uuid id PK  uuid membership_id FK  uuid role_id FK  string scope_type  uuid[] scope_refs  timestamptz valid_from  timestamptz valid_to }
  ROLE { uuid id PK  uuid tenant_id FK  string key  string name  bool system }
  ROLE_PERMISSION { uuid role_id FK  string permission_key }
  DEVICE { uuid id PK  uuid account_id FK  string platform  string push_token  timestamptz last_seen_at }
  TENANT_MODULE { uuid tenant_id FK  string module_key  bool enabled  jsonb settings }
  API_KEY { uuid id PK  uuid tenant_id FK  string hashed_key  string[] scopes  timestamptz expires_at }
  WEBHOOK_SUBSCRIPTION { uuid id PK  uuid tenant_id FK  string url  string[] event_types  string secret  bool active }
```

## 12.2 People and enrollment

```mermaid
erDiagram
  PERSON ||--o| STUDENT : is
  PERSON ||--o| STAFF : is
  PERSON ||--o| GUARDIAN : is
  GUARDIAN ||--o{ GUARDIAN_LINK : links
  STUDENT ||--o{ GUARDIAN_LINK : linked_by
  GUARDIAN_LINK ||--o{ CONSENT : records
  STUDENT ||--o{ ENROLLMENT : has
  HALAQAH ||--o{ ENROLLMENT : contains
  BRANCH ||--o{ HALAQAH : hosts
  STAFF ||--o{ HALAQAH_STAFF : assigned
  HALAQAH ||--o{ HALAQAH_STAFF : staffed_by
  STUDENT ||--o{ STUDENT_STATUS_EVENT : history
  APPLICANT ||--o| STUDENT : becomes
  WAITLIST_ENTRY }o--|| APPLICANT : for
  WAITLIST_ENTRY }o--|| HALAQAH : targets
  PERSON ||--o{ DOCUMENT : uploads

  PERSON { uuid id PK  uuid tenant_id FK  string first_name  string last_name  string display_name_ar  string display_name_en  date date_of_birth  string gender  string phone  citext email  jsonb address  string photo_key  string status }
  STUDENT { uuid id PK  uuid person_id FK  string student_code  uuid branch_id FK  string level  bool is_minor  string status "applicant|active|paused|left|alumni" }
  STAFF { uuid id PK  uuid person_id FK  string staff_type "teacher|assistant|supervisor|admin|finance|hr|instructor|support"  jsonb qualifications  string[] riwayat  jsonb availability  numeric max_load }
  GUARDIAN { uuid id PK  uuid person_id FK  jsonb communication_preferences }
  GUARDIAN_LINK { uuid id PK  uuid guardian_id FK  uuid student_id FK  string relationship  bool primary  bool finance_visibility  bool active }
  CONSENT { uuid id PK  uuid guardian_link_id FK  string consent_type "data_processing|media|asr|messaging|recording"  bool granted  timestamptz granted_at  string evidence_ref  string jurisdiction }
  HALAQAH { uuid id PK  uuid tenant_id FK  uuid branch_id FK  string name  string kind "in_person|online|hybrid"  string gender_policy  int capacity  uuid policy_id FK  string riwayah  string mushaf_type  string status }
  ENROLLMENT { uuid id PK  uuid student_id FK  uuid halaqah_id FK  date start_date  date end_date  string status  string reason }
  HALAQAH_STAFF { uuid halaqah_id FK  uuid staff_id FK  string role "teacher|assistant"  date from  date to }
  APPLICANT { uuid id PK  uuid tenant_id FK  jsonb form_data  string status  uuid placement_assessment_id }
  WAITLIST_ENTRY { uuid id PK  uuid applicant_id FK  uuid halaqah_id FK  int priority  timestamptz added_at }
```

## 12.3 Quran Core (read-only, versioned; not tenant-scoped)

```mermaid
erDiagram
  QC_RELEASE ||--o{ QC_RIWAYAH : includes
  QC_RIWAYAH ||--o{ QC_SURAH : has
  QC_RIWAYAH ||--o{ QC_AYAH : has
  QC_AYAH ||--o{ QC_WORD : contains
  QC_RIWAYAH ||--o{ QC_MUSHAF_LAYOUT : laid_out_as
  QC_MUSHAF_LAYOUT ||--o{ QC_PAGE : has
  QC_PAGE ||--o{ QC_LINE : has
  QC_LINE ||--o{ QC_WORD_PLACEMENT : places
  QC_WORD ||--o{ QC_WORD_PLACEMENT : placed
  QC_RIWAYAH ||--o{ QC_UNIT : divides
  QC_AYAH ||--o{ QC_MARKER : marked
  QC_RECITER ||--o{ QC_AUDIO_FILE : recorded
  QC_AUDIO_FILE ||--o{ QC_AUDIO_SEGMENT : timed
  QC_RIWAYAH ||--o{ QC_NUMBERING_MAP : maps
  QC_RELEASE ||--o{ QC_MUTASHABIHAT_GROUP : includes
  QC_MUTASHABIHAT_GROUP ||--o{ QC_MUTASHABIHAT_MEMBER : has

  QC_RELEASE { string version PK  timestamptz built_at  jsonb sources  jsonb checksums  string signature  string[] reviewers }
  QC_RIWAYAH { string key PK  string version FK  string reader  string transmitter  bool available  int ayah_count }
  QC_SURAH { int number PK  string riwayah FK  string name_ar  string name_en  string revelation  int ayah_count }
  QC_AYAH { string riwayah FK  int surah  int ayah  int ayah_index  text text_uthmani  text text_simple  string sha256 }
  QC_WORD { string riwayah FK  int ayah_index  int position  text text  string glyph_code  string root  string lemma }
  QC_MUSHAF_LAYOUT { string key PK  string riwayah FK  int pages  int lines_per_page  string font_pack }
  QC_PAGE { string layout FK  int page  int first_ayah_index  int last_ayah_index  int juz }
  QC_UNIT { string riwayah FK  string unit_type "juz|hizb|rub|manzil"  int number  int first_ayah_index  int last_ayah_index }
  QC_MARKER { string riwayah FK  int ayah_index  int word_position  string marker_type "sajdah|waqf|saktah"  string value }
  QC_RECITER { string key PK  string name_ar  string name_en  string riwayah  string style  string license_status  jsonb provenance  string audio_version }
  QC_AUDIO_FILE { uuid id PK  string reciter FK  int surah  string object_key  int duration_ms  string sha256  int bitrate }
  QC_AUDIO_SEGMENT { uuid audio_file_id FK  int ayah_index  int word_position  int start_ms  int end_ms }
  QC_NUMBERING_MAP { string from_riwayah  int from_ayah_index  string to_riwayah  int to_ayah_index }
  QC_MUTASHABIHAT_GROUP { uuid id PK  string version FK  string provenance  string review_status }
  QC_MUTASHABIHAT_MEMBER { uuid group_id FK  int ayah_index  int[] differing_word_positions }
```

## 12.4 Quran learning (journey, memory map, retention, planning, Tasmee')

```mermaid
erDiagram
  STUDENT ||--|| QURAN_JOURNEY : has
  QURAN_JOURNEY ||--o{ JOURNEY_EVENT : timeline
  QURAN_JOURNEY ||--o{ STUDENT_AYAH_STATE : map
  STUDENT_AYAH_STATE ||--o{ AYAH_STATE_EVENT : history
  QURAN_JOURNEY ||--o{ RETENTION_SNAPSHOT : monthly
  LEARNING_POLICY ||--o{ POLICY_ASSIGNMENT : applied
  QURAN_JOURNEY ||--o{ DAILY_PLAN : planned
  DAILY_PLAN ||--o{ PLAN_SEGMENT : contains
  DAILY_PLAN ||--o{ PLAN_ACTION : teacher_actions
  QURAN_JOURNEY ||--o{ RECITATION_SESSION : recited
  RECITATION_SESSION ||--o{ RECITATION_SEGMENT : covers
  RECITATION_SESSION ||--o{ MISTAKE_EVENT : mistakes
  RECITATION_SESSION }o--o| LIVE_SESSION : during
  ASSESSMENT_DEFINITION ||--o{ ASSESSMENT : instances
  ASSESSMENT ||--|| RECITATION_SESSION : recorded_as
  QURAN_JOURNEY ||--o{ PRACTICE_SESSION : practiced
  PRACTICE_SESSION ||--o{ PRACTICE_EVENT : events
  PRACTICE_SESSION ||--o{ REVIEW_QUEUE_ITEM : flagged
  REVIEW_QUEUE_ITEM ||--o| DETECTOR_FEEDBACK : verdict
  QURAN_JOURNEY ||--o{ STUDENT_MUTASHABIHAT_ITEM : personal_set
  MISTAKE_TYPE ||--o{ MISTAKE_EVENT : classifies
  QURAN_JOURNEY ||--o{ IJAZAH_RECORD : granted
  QURAN_JOURNEY ||--o{ CERTIFICATE : awarded

  QURAN_JOURNEY { uuid id PK  uuid student_id FK  string riwayah  string mushaf_type  string status  date started_at  string direction  int current_ayah_index  int level  numeric velocity_pages_wk  numeric revision_compliance  string qc_version }
  JOURNEY_EVENT { uuid id PK  uuid journey_id FK  string event_type  jsonb payload  timestamptz occurred_at  uuid actor_id }
  STUDENT_AYAH_STATE { uuid journey_id FK  int ayah_index  string state  numeric retention_score  numeric stability_days  timestamptz last_recited_at  timestamptz last_passed_at  timestamptz memorized_at  int success_count  int fail_count  int mistakes_30d  timestamptz next_due_at  string engine_version  uuid override_by }
  AYAH_STATE_EVENT { uuid id PK  uuid journey_id FK  int ayah_index  string prev_state  string new_state  numeric prev_score  numeric new_score  string cause  uuid cause_ref  string engine_version  timestamptz occurred_at }
  RETENTION_SNAPSHOT { uuid journey_id FK  date snapshot_date  int juz  numeric avg_retention  int weak_ayat  int critical_ayat }
  LEARNING_POLICY { uuid id PK  uuid tenant_id FK  string key  int version  jsonb spec  string status }
  POLICY_ASSIGNMENT { uuid id PK  uuid policy_id FK  string target_type "tenant|branch|halaqah|student"  uuid target_id  date from  date to }
  DAILY_PLAN { uuid id PK  uuid journey_id FK  date plan_date  string status "proposed|approved|edited|overridden|done|carried"  jsonb rationale  uuid approved_by }
  PLAN_SEGMENT { uuid id PK  uuid plan_id FK  string purpose "new|near|far|mutashabihat|assessment"  int from_ayah_index  int to_ayah_index  int repetitions_required  string completion "pending|self_reported|verified" }
  PLAN_ACTION { uuid id PK  uuid plan_id FK  string action  jsonb before  jsonb after  uuid actor_id  timestamptz at }
  RECITATION_SESSION { uuid id PK  uuid journey_id FK  uuid teacher_id FK  uuid halaqah_id FK  string purpose  timestamptz started_at  timestamptz ended_at  string outcome "pass|repeat|partial"  numeric grade  text note  string note_visibility  string source "in_person|live|review_queue|assessment"  string idempotency_key }
  RECITATION_SEGMENT { uuid session_id FK  int from_ayah_index  int to_ayah_index  int repetitions }
  MISTAKE_EVENT { uuid id PK  uuid session_id FK  int ayah_index  int word_position  string mistake_type_key FK  string severity  int confused_with_ayah_index  text note  timestamptz at }
  MISTAKE_TYPE { string key PK  uuid tenant_id FK "null for standard"  string name  numeric default_weight  string default_severity }
  ASSESSMENT_DEFINITION { uuid id PK  uuid tenant_id FK  string name  jsonb scope  jsonb rubric  int passing_score  bool blind_second_examiner }
  ASSESSMENT { uuid id PK  uuid definition_id FK  uuid journey_id FK  uuid examiner_id  uuid second_examiner_id  timestamptz scheduled_at  numeric score  string result  jsonb feedback }
  PRACTICE_SESSION { uuid id PK  uuid journey_id FK  int from_ayah_index  int to_ayah_index  string mode  int hints_used  timestamptz started_at  timestamptz ended_at  bool self_reported_complete }
  PRACTICE_EVENT { uuid session_id FK  string event_type "hint_text|hint_audio|reveal|repeat|quiz_answer"  int ayah_index  jsonb payload  timestamptz at }
  REVIEW_QUEUE_ITEM { uuid id PK  uuid journey_id FK  uuid practice_session_id FK  int surah  int ayah  int start_ms  int end_ms  string suspected_issue  numeric confidence  string clip_key  timestamptz clip_expires_at  string status }
  DETECTOR_FEEDBACK { uuid item_id FK  uuid teacher_id  string verdict  string mistake_type_key  text note  timestamptz at  string provider_key  string model_version }
  STUDENT_MUTASHABIHAT_ITEM { uuid id PK  uuid journey_id FK  uuid group_id  int ayah_a  int ayah_b  int confusion_count  timestamptz last_confused_at  string status }
  IJAZAH_RECORD { uuid id PK  uuid journey_id FK  uuid grantor_staff_id FK  string riwayah  string scope  date granted_on  jsonb chain_notes  uuid[] witness_ids  uuid[] supporting_assessment_ids  uuid supersedes_id }
  CERTIFICATE { uuid id PK  uuid tenant_id FK  uuid student_id FK  string kind "hifz_milestone|course|assessment"  uuid template_id  string verification_code  timestamptz issued_at  uuid issued_by  string pdf_key }
```

## 12.5 Content library, Tafsir, Hadith

```mermaid
erDiagram
  CONTENT_WORK ||--o{ CONTENT_ITEM : contains
  CONTENT_ITEM ||--o{ CONTENT_VERSION : versions
  CONTENT_ITEM ||--o{ AYAH_LINK : linked_to
  CONTENT_WORK ||--|| PROVENANCE : has
  CONTENT_ITEM ||--o{ CONTENT_REVIEW : reviewed
  HADITH_COLLECTION ||--o{ HADITH_BOOK : has
  HADITH_BOOK ||--o{ HADITH_CHAPTER : has
  HADITH_CHAPTER ||--o{ HADITH : has
  HADITH ||--o{ HADITH_TRANSLATION : translated
  HADITH ||--o{ HADITH_GRADING : graded
  HADITH ||--o{ HADITH_TOPIC : tagged
  CONTENT_ITEM ||--o{ BOOKMARK : bookmarked
  CONTENT_ITEM ||--o{ USER_NOTE : annotated

  CONTENT_WORK { uuid id PK  uuid tenant_id FK "null = platform library"  string content_class "canonical|scholarly|center_created|ai_generated"  string content_type "tafsir|tajweed|arabic|quran_science|fiqh|aqeedah|seerah|manners|custom"  string title  string language  string author  string source  string edition  string publisher  string license  string license_status  string verification_status  int version }
  PROVENANCE { uuid work_id FK  string source_url  timestamptz retrieved_at  string checksum  string reviewer  timestamptz reviewed_at  text notes }
  CONTENT_ITEM { uuid id PK  uuid work_id FK  string item_type "ayah_commentary|surah_intro|lesson|article|rule|vocab"  text body  jsonb structured  string status }
  CONTENT_VERSION { uuid id PK  uuid item_id FK  int version  text body  uuid editor_id  timestamptz at  text change_note }
  AYAH_LINK { uuid item_id FK  string riwayah  int from_ayah_index  int to_ayah_index }
  HADITH_COLLECTION { uuid id PK  string key  string name_ar  string name_en  string source  string license  string license_status }
  HADITH { uuid id PK  uuid chapter_id FK  int number  text text_ar  string narrator  string isnad_summary  string source_ref }
  HADITH_GRADING { uuid hadith_id FK  string grade  string scholar  string source  string provider  string license_status }
  HADITH_TRANSLATION { uuid hadith_id FK  string language  text text  string translator  string license }
```

AI-generated assistance (summaries, transcriptions) is stored in `GENERATED_TEXT { id, tenant_id, purpose, provider_key, model_version, source_refs[], text, created_at }` with a non-null `source_refs` constraint for summaries; it can never be linked as a `CONTENT_WORK` of class `canonical` or `scholarly`.

## 12.6 Courses (LMS), exams, homework

```mermaid
erDiagram
  COURSE ||--o{ COURSE_MODULE : has
  COURSE_MODULE ||--o{ LESSON : has
  LESSON ||--o{ LESSON_RESOURCE : includes
  COURSE ||--o{ COHORT : runs
  COHORT ||--o{ COURSE_ENROLLMENT : enrolls
  STUDENT ||--o{ COURSE_ENROLLMENT : takes
  COURSE_ENROLLMENT ||--o{ LESSON_PROGRESS : tracks
  LESSON ||--o{ ASSIGNMENT : sets
  ASSIGNMENT ||--o{ SUBMISSION : receives
  QUESTION_BANK ||--o{ QUESTION : holds
  QUIZ ||--o{ QUIZ_QUESTION : uses
  QUIZ ||--o{ QUIZ_ATTEMPT : attempted
  COURSE ||--o{ COURSE_PREREQUISITE : requires
  LEARNING_PATH ||--o{ LEARNING_PATH_STEP : orders
  LESSON }o--o| LIVE_SESSION : delivered_live

  COURSE { uuid id PK  uuid tenant_id FK  string title  string subject  string mode "self_paced|scheduled|live|hybrid"  string status  uuid instructor_id  jsonb certificate_rule }
  LESSON { uuid id PK  uuid module_id FK  string title  string kind "reading|video|audio|pdf|live|quiz|assignment"  jsonb content_ref  int order }
  ASSIGNMENT { uuid id PK  uuid lesson_id FK  string title  timestamptz due_at  jsonb spec  bool parent_visible }
  SUBMISSION { uuid id PK  uuid assignment_id FK  uuid student_id FK  jsonb files  numeric grade  text feedback  string status }
  QUESTION { uuid id PK  uuid bank_id FK  string kind  jsonb body  jsonb answer  string content_class }
```

Deterministic Quran quizzes reference Quran Core by `ayah_index` and generate options from verified text only (`QUESTION.content_class = canonical_derived`).

## 12.7 Scheduling, attendance, live sessions

```mermaid
erDiagram
  SCHEDULE_SERIES ||--o{ SESSION_OCCURRENCE : generates
  SESSION_OCCURRENCE ||--o{ ATTENDANCE_RECORD : records
  SESSION_OCCURRENCE }o--o| ROOM : in
  SESSION_OCCURRENCE }o--o| LIVE_SESSION : online
  LIVE_SESSION ||--o{ LIVE_PARTICIPATION : joins
  LIVE_SESSION ||--o{ LIVE_ROSTER_STATE : states
  CALENDAR ||--o{ CALENDAR_EVENT : has
  STAFF ||--o{ LEAVE : takes
  SESSION_OCCURRENCE }o--o| SUBSTITUTION : substituted

  SCHEDULE_SERIES { uuid id PK  uuid tenant_id FK  uuid branch_id FK  string target_type "halaqah|course|one_to_one|office_hours"  uuid target_id  string rrule  string timezone  time start_time  int duration_min  uuid room_id  uuid teacher_id  date from  date until }
  SESSION_OCCURRENCE { uuid id PK  uuid series_id FK  timestamptz starts_at  timestamptz ends_at  string status "scheduled|held|cancelled|makeup"  uuid teacher_id  uuid room_id  uuid makeup_for_id }
  ATTENDANCE_RECORD { uuid id PK  uuid occurrence_id FK  uuid student_id FK  string status "present|absent|late|excused|left_early"  string reason  timestamptz marked_at  uuid marked_by  string source "manual|live_auto|qr" }
  LIVE_SESSION { uuid id PK  uuid occurrence_id FK  string provider_key  string room_key  string status  bool recording_allowed  string video_policy  timestamptz opened_at  timestamptz closed_at  jsonb quality_stats }
  LIVE_PARTICIPATION { uuid id PK  uuid live_session_id FK  uuid person_id FK  string role  timestamptz joined_at  timestamptz left_at  int reconnects  string region }
  LIVE_ROSTER_STATE { uuid live_session_id FK  uuid student_id FK  string state  timestamptz at }
  ROOM { uuid id PK  uuid branch_id FK  string name  int capacity  jsonb equipment }
  CALENDAR { uuid id PK  uuid tenant_id FK  uuid branch_id FK  string name  string calendar_system }
  CALENDAR_EVENT { uuid id PK  uuid calendar_id FK  string kind "holiday|term|exam|event"  date from  date to }
  LEAVE { uuid id PK  uuid staff_id FK  date from  date to  string status }
  SUBSTITUTION { uuid id PK  uuid occurrence_id FK  uuid original_teacher_id  uuid substitute_id  string reason }
```

## 12.8 Finance

```mermaid
erDiagram
  FEE_STRUCTURE ||--o{ FEE_PLAN : offers
  FEE_PLAN ||--o{ STUDENT_FEE_PLAN : assigned
  STUDENT ||--o{ STUDENT_FEE_PLAN : pays_under
  STUDENT_FEE_PLAN ||--o{ INVOICE : generates
  INVOICE ||--o{ INVOICE_LINE : has
  INVOICE ||--o{ PAYMENT_ALLOCATION : settled_by
  PAYMENT ||--o{ PAYMENT_ALLOCATION : allocates
  PAYMENT ||--o| RECEIPT : issues
  PAYMENT }o--o| REFUND : refunded
  DISCOUNT ||--o{ INVOICE_LINE : applied
  SCHOLARSHIP ||--o{ STUDENT_FEE_PLAN : funds
  DONATION_CAMPAIGN ||--o{ DONATION : receives
  DONATION }o--o| SPONSORSHIP : sponsors
  SPONSORSHIP }o--|| STUDENT : for
  EXPENSE_CATEGORY ||--o{ EXPENSE : classifies
  STAFF ||--o{ PAYOUT : paid
  PAYOUT ||--o{ PAYOUT_LINE : has

  FEE_STRUCTURE { uuid id PK  uuid tenant_id FK  string name  string currency  jsonb rules }
  FEE_PLAN { uuid id PK  uuid structure_id FK  string name  string cadence "monthly|term|annual|per_session"  numeric amount  jsonb sibling_rules }
  INVOICE { uuid id PK  uuid tenant_id FK  uuid branch_id FK  string number  uuid payer_person_id  numeric total  numeric paid  string currency  string status "draft|issued|partially_paid|paid|overdue|void"  date due_date  string pdf_key }
  PAYMENT { uuid id PK  uuid tenant_id FK  string method "cash|bank_transfer|gateway"  string gateway_key  string gateway_ref  numeric amount  string currency  string status  timestamptz received_at  string proof_key  string idempotency_key }
  RECEIPT { uuid id PK  uuid payment_id FK  string number  string pdf_key }
  DONATION { uuid id PK  uuid tenant_id FK  uuid campaign_id FK  uuid donor_person_id  numeric amount  string currency  bool anonymous  string receipt_key }
  EXPENSE { uuid id PK  uuid tenant_id FK  uuid branch_id FK  uuid category_id FK  numeric amount  string currency  date on  string status  uuid approved_by  string attachment_key }
  PAYOUT { uuid id PK  uuid staff_id FK  string period  numeric amount  string currency  string basis "per_session|hourly|salary"  string status }
```

## 12.9 Communication, notifications, intelligence, audit, portability

```mermaid
erDiagram
  NOTIFICATION_TEMPLATE ||--o{ NOTIFICATION : instantiates
  NOTIFICATION ||--o{ NOTIFICATION_DELIVERY : delivered_via
  ACCOUNT ||--o{ NOTIFICATION_PREFERENCE : sets
  MESSAGE_THREAD ||--o{ MESSAGE : contains
  MESSAGE_THREAD ||--o{ THREAD_PARTICIPANT : includes
  ANNOUNCEMENT ||--o{ ANNOUNCEMENT_READ : read_by
  INTERVENTION_FLAG ||--o{ INTERVENTION_ACTION : actions
  INTERVENTION_FLAG ||--o{ INTERVENTION_SIGNAL : evidence
  STUDENT ||--o{ INTERVENTION_FLAG : flagged
  STUDENT ||--o{ WEEKLY_REPORT : receives
  AUDIT_LOG }o--|| TENANT : scoped
  QLR_EXPORT }o--|| STUDENT : of
  QLR_IMPORT }o--|| STUDENT : into
  OUTBOX_EVENT }o--|| TENANT : scoped

  NOTIFICATION { uuid id PK  uuid tenant_id FK  uuid recipient_account_id  string event_type  jsonb payload  string priority  timestamptz created_at }
  NOTIFICATION_DELIVERY { uuid id PK  uuid notification_id FK  string channel "push|email|sms|whatsapp|in_app"  string provider_key  string status  string provider_ref  timestamptz sent_at  text error }
  MESSAGE_THREAD { uuid id PK  uuid tenant_id FK  string kind "teacher_guardian|staff|announcement_reply|supervised_student"  uuid student_context_id  string policy_snapshot }
  MESSAGE { uuid id PK  uuid thread_id FK  uuid sender_id  text body  jsonb attachments  timestamptz at  bool flagged }
  INTERVENTION_FLAG { uuid id PK  uuid student_id FK  string level "watch|attention|urgent"  numeric score  jsonb explanation  string status  uuid owner_id  timestamptz opened_at  timestamptz closed_at  string outcome }
  INTERVENTION_SIGNAL { uuid flag_id FK  string signal_key  numeric value  numeric weight  jsonb evidence }
  INTERVENTION_ACTION { uuid id PK  uuid flag_id FK  string action_type  uuid assignee_id  string status  text notes  timestamptz due_at }
  WEEKLY_REPORT { uuid id PK  uuid student_id FK  date week_start  jsonb metrics  text teacher_note  timestamptz generated_at  timestamptz viewed_at }
  AUDIT_LOG { uuid id PK  uuid tenant_id FK  uuid actor_id  string actor_type  string action  string object_type  uuid object_id  jsonb before  jsonb after  inet ip  string device  timestamptz at  string request_id }
  OUTBOX_EVENT { uuid id PK  uuid tenant_id FK  string event_type  jsonb payload  timestamptz created_at  timestamptz published_at }
  QLR_EXPORT { uuid id PK  uuid student_id FK  string spec_version  jsonb privacy_options  string file_key  string signature  uuid requested_by  timestamptz at }
  QLR_IMPORT { uuid id PK  uuid student_id FK  string source_institution  string spec_version  jsonb mapping  string verification_status  timestamptz at }
```

## 12.10 Key indexes and partitioning

- `STUDENT_AYAH_STATE (journey_id, ayah_index)` primary key; partial indexes on `next_due_at` and on `state IN ('weak','critical')`.
- `AYAH_STATE_EVENT`, `MISTAKE_EVENT`, `AUDIT_LOG`, `NOTIFICATION_DELIVERY`: monthly range partitions by `occurred_at`/`at`; `tenant_id` in every index.
- `RECITATION_SESSION (journey_id, started_at desc)`; `ATTENDANCE_RECORD (occurrence_id, student_id)` unique.
- `INVOICE (tenant_id, number)` unique; sequences per tenant via a `NUMBER_SEQUENCE` table.
- RLS policies on every tenant table; Quran Core tables have no `tenant_id` and are `SELECT`-only for the app role.

## 12.11 Retention and privacy fields

Tables holding media or minors' data carry `retention_until` and a `purge_job` handles deletion: `REVIEW_QUEUE_ITEM.clip_*` (default 30 days), `PRACTICE_EVENT` audio references (not retained by default), `LIVE_SESSION` recordings (only if allowed, tenant-defined), `MESSAGE.attachments`. Exports and deletions of a person are orchestrated through `DATA_SUBJECT_REQUEST { id, tenant_id, person_id, kind "export|delete", status, completed_at, bundle_key }`.
