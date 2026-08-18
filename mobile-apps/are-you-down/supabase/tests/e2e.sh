#!/usr/bin/env bash
# End-to-end checks against the running local Supabase, through PostgREST,
# using real user JWTs — i.e. the exact path the app takes.
set -euo pipefail

API=http://127.0.0.1:54321
ANON="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"

pass=0; fail=0

token_for() {
  curl -s -X POST "$API/auth/v1/token?grant_type=password" \
    -H "apikey: $ANON" -H "Content-Type: application/json" \
    -d "{\"email\":\"$1\",\"password\":\"password123\"}" |
    python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))"
}

check() { # label actual expected
  if [ "$2" = "$3" ]; then echo "ok   $1 ($2)"; pass=$((pass+1));
  else echo "FAIL $1 — expected $3, got $2"; fail=$((fail+1)); fi
}

jlen() { python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 'ERROR:'+str(d.get('message','?')))"; }

JON=$(token_for jonathan@ucmerced.edu)
PRIYA=$(token_for priya@ucmerced.edu)
RAVI=$(token_for ravi@sjsu.edu)

[ -n "$JON" ] || { echo "FAIL could not sign in"; exit 1; }
echo "ok   password sign-in works for seeded users"; pass=$((pass+1))

get() { curl -s "$API/rest/v1/$1" -H "apikey: $ANON" -H "Authorization: Bearer $2"; }
rpc() { local body="${3:-}"; [ -z "$body" ] && body='{}'
        curl -s -X POST "$API/rest/v1/rpc/$1" -H "apikey: $ANON" -H "Authorization: Bearer $2" \
          -H "Content-Type: application/json" -d "$body"; }

check "feed returns the right drops"        "$(rpc get_feed "$JON" | jlen)" 6

# Group filter, through PostgREST rather than a direct call: the named-argument
# path is what the app actually uses, and a signature mismatch fails here first.
check "feed filtered to one group"          "$(rpc get_feed "$JON" '{"p_group":"errands"}' | jlen)" 2
check "the groups add up to the whole feed" \
  "$(for g in food move chill study out errands; do rpc get_feed "$JON" "{\"p_group\":\"$g\"}" | jlen; done |
     python3 -c "import sys; print(sum(int(n) for n in sys.stdin))")" 6
check "unknown group returns nothing"       "$(rpc get_feed "$JON" '{"p_group":"nope"}' | jlen)" 0
check "threads list"                        "$(rpc get_threads "$JON" | jlen)" 1
check "own responses readable"              "$(get 'responses?select=type' "$JON" | jlen)" 3
check "author sees no responses to theirs"  "$(get 'responses?select=type' "$PRIYA" | jlen)" 0
check "campus scoping on drops (UC Merced)" "$(get 'drops?select=id' "$JON" | jlen)" 12
check "campus scoping on drops (SJSU)"      "$(get 'drops?select=id' "$RAVI" | jlen)" 3
check "messages visible to a member"        "$(get 'messages?select=id' "$JON" | jlen)" 3
check "messages hidden from a non-member"   "$(get 'messages?select=id' "$RAVI" | jlen)" 0
check "schools readable without a session"  "$(curl -s "$API/rest/v1/schools?select=id" -H "apikey: $ANON" | jlen)" 2
check "drops NOT readable without session"  "$(curl -s "$API/rest/v1/drops?select=id" -H "apikey: $ANON" | python3 -c "import sys,json; d=json.load(sys.stdin); print('denied' if isinstance(d,dict) else 'LEAKED '+str(len(d)))")" denied
check "reports are not readable"            "$(get 'reports?select=id' "$JON" | python3 -c "import sys,json; d=json.load(sys.stdin); print('denied' if isinstance(d,dict) else len(d))")" denied

# Posting a drop, then answering it as someone else, should build a thread.
NEW=$(curl -s -X POST "$API/rest/v1/drops" -H "apikey: $ANON" -H "Authorization: Bearer $JON" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d "{\"user_id\":\"b0000000-0000-4000-8000-000000000001\",\"school_id\":\"a0000000-0000-4000-8000-000000000001\",\"body\":\"e2e test drop\",\"category\":\"food\",\"expires_at\":\"$(date -u -v+1H '+%Y-%m-%dT%H:%M:%SZ')\"}" |
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if isinstance(d,list) and d else 'ERR:'+str(d))")
check "created a drop" "$(echo "$NEW" | grep -c '^ERR' || true)" 0

RESP=$(curl -s -X POST "$API/rest/v1/responses" -H "apikey: $ANON" -H "Authorization: Bearer $PRIYA" \
  -H "Content-Type: application/json" -H "Prefer: return=representation" \
  -d "{\"drop_id\":\"$NEW\",\"user_id\":\"b0000000-0000-4000-8000-000000000004\",\"type\":\"down\"}")
check "responding down succeeds" "$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if isinstance(d,list) else d.get('message','?'))")" ok
check "thread now exists for the author" "$(rpc get_threads "$JON" | jlen)" 2
check "and for the responder"            "$(rpc get_threads "$PRIYA" | jlen)" 2

# Second response from the same user must be refused.
DUP=$(curl -s -X POST "$API/rest/v1/responses" -H "apikey: $ANON" -H "Authorization: Bearer $PRIYA" \
  -H "Content-Type: application/json" \
  -d "{\"drop_id\":\"$NEW\",\"user_id\":\"b0000000-0000-4000-8000-000000000004\",\"type\":\"pass\"}" |
  python3 -c "import sys,json; print(json.load(sys.stdin).get('code','none'))")
check "duplicate response rejected" "$DUP" 23505

# Cross-campus answer must be refused.
XC=$(curl -s -X POST "$API/rest/v1/responses" -H "apikey: $ANON" -H "Authorization: Bearer $RAVI" \
  -H "Content-Type: application/json" \
  -d "{\"drop_id\":\"$NEW\",\"user_id\":\"b0000000-0000-4000-8000-000000000011\",\"type\":\"down\"}" |
  python3 -c "import sys,json; print(json.load(sys.stdin).get('message','none'))")
check "cross-campus response rejected" "$XC" "That drop is not from your campus."

# The GIF proxy. Deliberately not asserting 200: without a TENOR_API_KEY the
# function answers 503 and the picker says so, which is a configured state, not
# a broken one. A 404 is the broken one — the function isn't being served at
# all, which is exactly how "the GIF system does nothing" looked.
GIF=$(curl -s -o /dev/null -w '%{http_code}' "$API/functions/v1/gif-search?q=boba" \
  -H "apikey: $ANON" -H "Authorization: Bearer $JON")
check "gif proxy is served" "$([ "$GIF" = 404 ] && echo missing || echo served)" served

echo
echo "passed: $pass   failed: $fail"
[ "$fail" -eq 0 ]
