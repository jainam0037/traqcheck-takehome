-- Minimal schema
create table candidates(
  id uuid primary key,
  name text, email text, phone text,
  company text, designation text,
  skills jsonb default '[]',
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table resumes(
  id uuid primary key,
  candidate_id uuid references candidates(id) on delete cascade,
  file_url text, mime text, sha256 text,
  created_at timestamptz default now()
);

create table extractions(
  id uuid primary key,
  candidate_id uuid references candidates(id) on delete cascade,
  status text check (status in ('queued','done','error')) default 'queued',
  raw_text text,
  extracted_json jsonb, confidence_json jsonb,
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table document_requests(
  id uuid primary key,
  candidate_id uuid references candidates(id) on delete cascade,
  channel text check (channel in ('email','sms')),
  payload_json jsonb,
  created_at timestamptz default now()
);

create table documents(
  id uuid primary key,
  candidate_id uuid references candidates(id) on delete cascade,
  type text check (type in ('PAN','AADHAAR')),
  file_url text, verified boolean default false,
  uploaded_at timestamptz default now()
);

create table audit_logs(
  id uuid primary key,
  actor text, action text,
  candidate_id uuid references candidates(id) on delete cascade,
  metadata jsonb, ts timestamptz default now()
);
