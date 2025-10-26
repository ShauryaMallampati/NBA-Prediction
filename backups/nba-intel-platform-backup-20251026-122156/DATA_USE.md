# Data Use & Ethics Guidelines

## Overview

The NBA Intelligence Platform uses real data from multiple sources. This document outlines ethical guidelines, compliance requirements, and best practices.

## Data Sources & Compliance

### NBA Stats API
- **Terms**: Respect rate limits (100-500 req/day)
- **Attribution**: Credit NBA Stats API in any public use
- **Restrictions**: Non-commercial use only (free tier)

### Basketball-Reference
- **Terms**: Respect robots.txt and rate limits (3s between requests)
- **Attribution**: Required for any scraped data
- **Restrictions**: No automated scraping without permission

### Social Media APIs

#### Twitter/X
- **Terms**: Follow Twitter Developer Agreement
- **Data Retention**: Delete tweets if requested by users
- **Privacy**: Do not store PII; aggregate only
- **Rate Limits**: 500k-2M tweets/month depending on tier

#### Reddit
- **Terms**: Follow Reddit API Terms
- **Rate Limits**: 60 requests/minute
- **Privacy**: Public posts only; no user tracking

#### YouTube
- **Terms**: Follow YouTube API Terms of Service
- **Rate Limits**: 10,000 units/day
- **Privacy**: Public videos only

### OpenRouteService
- **Terms**: Free tier for non-commercial use
- **Rate Limits**: 2,000 requests/day
- **Attribution**: Required in public applications

## Privacy & PII

### What We Collect
- Public game statistics
- Public social media posts (aggregated)
- Team and player performance metrics

### What We DON'T Collect
- Personal contact information
- Private messages or DMs
- User location data
- Financial information

### Aggregation
- Social sentiment is aggregated at team/player level
- Individual posts are not stored long-term
- No user profiling or tracking

## Ethical Use

### DO
✓ Use for research and education  
✓ Aggregate social data for sentiment analysis  
✓ Respect rate limits and ToS  
✓ Attribute data sources  
✓ Monitor for bias and fairness  

### DON'T
✗ Use for gambling or betting  
✗ Store PII or private data  
✗ Violate API terms of service  
✗ Scrape aggressively or without permission  
✗ Use for player harassment or discrimination  

## Bias & Fairness

### Known Biases
- Historical data may reflect systemic biases in player evaluation
- Social sentiment may amplify popular narratives
- Market odds (if used) reflect betting markets, not ground truth

### Mitigations
- Diverse feature sets (not just social signals)
- Calibrated probabilities to avoid overconfidence
- Regular audits for fairness across teams/players
- Transparency in model limitations

## Research Use Only

This platform is intended for:
- Academic research
- Sports analytics education
- Personal learning and experimentation

It is NOT intended for:
- Commercial gambling or betting
- Official game officiating
- Player contract negotiations
- Any use that could harm individuals

## Compliance Checklist

Before deploying or sharing this platform:

- [ ] All API keys are valid and within rate limits
- [ ] Data sources are properly attributed
- [ ] Social data is aggregated (no PII stored)
- [ ] Terms of Service are respected for all APIs
- [ ] Users are warned about research-only use
- [ ] Model limitations are clearly documented
- [ ] Bias and fairness have been considered

## Contact

For questions about data use or ethics, please open a GitHub issue or contact the maintainers.

## References

- [Twitter Developer Agreement](https://developer.twitter.com/en/developer-terms/agreement)
- [Reddit API Terms](https://www.reddit.com/wiki/api-terms)
- [YouTube API Terms](https://developers.google.com/youtube/terms/api-services-terms-of-service)
- [Basketball-Reference Terms](https://www.sports-reference.com/data_use.html)
