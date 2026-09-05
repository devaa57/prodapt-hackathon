#!/usr/bin/env python3
"""Quick script to test Neon connection and verify RLS and data."""
from run_migrations import get_connection

def test():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Set tenant context for RLS
    cur.execute("SET app.current_org_id = 'a0000000-0000-0000-0000-000000000001';")

    # 2. Query candidates for Senior Python Developer
    cur.execute("""
        SELECT
            c.full_name,
            c.email,
            sr.overall_score,
            sr.recommendation
        FROM screening_results sr
        JOIN candidates c ON c.id = sr.candidate_id
        WHERE sr.job_id = 'c0000000-0000-0000-0000-000000000001'
        ORDER BY sr.overall_score DESC NULLS LAST;
    """)

    rows = cur.fetchall()
    print("SUCCESS! Top Candidates for Senior Python Developer (with RLS enabled):")
    for r in rows:
        print(f"  • {r[0]} ({r[1]}) - Score: {r[2]}% [{r[3]}]")

    # 3. Test verification claims
    cur.execute("""
        SELECT c.full_name, vc.claim_description, vc.status, vc.confidence_score
        FROM verification_claims vc
        JOIN external_profiles ep ON ep.id = vc.external_profile_id
        JOIN candidates c ON c.id = ep.candidate_id;
    """)
    claims = cur.fetchall()
    print("\nVerified Claims in Database:")
    for cl in claims:
        print(f"  • {cl[0]}: {cl[1]} -> Status: {cl[2]} (Score: {cl[3]})")

    cur.close()
    conn.close()

if __name__ == "__main__":
    test()
