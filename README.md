# 香港直資及私立小學全攻略 2025/26

> 全港直資及私立小學資料庫，涵蓋荃灣、葵青及全港各區。

🔗 **Live site:** `https://<your-github-username>.github.io/hk-schools-guide/`

## Features

- **School database** — filter by type, district, gender, through-train, fee range, fee waiver
- **Side-by-side compare mode** — tick 2–4 schools → floating bar → full comparison panel with colour highlighting
- **Interview guide** — 6 top schools with scoring breakdown, interview steps, sample questions, tips
- **Study tips** — timeline, preparation checklist, DSS vs private guide

## Districts covered

| District | Schools |
|----------|---------|
| 港島區 | SPCC, SPC Primary, DGJS, ISF, VSA, Kau Yan, SSCPS, HKUGAPS |
| 九龍區 | DBS Primary, Pui Ching, PLK Choi Kai Yau, Ying Wa, Kowloon Tong |
| 荃灣區 | Sear Rogers International, Creative Ma Wan, 博愛醫院陳國威小學 |
| 葵青區 | Canaan Christian PS, Delia Man Kiu, HKTA Shek Wai Kok |
| 新界其他 | Logos Academy, Lutheran Academy, Malvern College HK |

## How to deploy (GitHub Pages)

```bash
# 1. Create a new GitHub repo named: hk-schools-guide
# 2. Push this project
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/hk-schools-guide.git
git push -u origin main

# 3. Enable GitHub Pages
# Go to: Settings → Pages → Source → GitHub Actions
# The workflow in .github/workflows/deploy.yml handles the rest automatically
```

Your site will be live at:
```
https://<YOUR_USERNAME>.github.io/hk-schools-guide/
```

## To add more schools (in Claude Code)

```
# Add schools from a specific district
"Add all private and DSS primary schools in Sha Tin district to index.html,
following the existing school object schema in the S array"

# Enrich missing data
"Search for teacher counts and campus areas for schools where
teachers or area fields are null in the S array"

# Add interview data
"Search for recent 2024–2025 interview reports for 聖士提反書院附屬小學
from baby kingdom and champimom, and add to its qs and tips arrays"
```

## Data sources

- [香港教育局校網名單](https://www.edb.gov.hk/en/student-parents/sch-info/sch-search/schlist-by-district/)
- [schooland.hk](https://www.schooland.hk/ps/private) — fees and class structure
- [topschool.hket.com](https://topschool.hket.com) — rankings and interview info
- [kidemy.hk](https://www.kidemy.hk) — interview breakdowns
- [chsc.hk](https://www.chsc.hk) — official school profiles (家校會)

## License

MIT — data sourced from public EDB records and school websites.
