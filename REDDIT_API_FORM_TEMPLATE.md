# Reddit API Access Request Form - Complete Template

Use this template to fill out the Reddit API access request form. Copy and paste the responses below.

## Form Fields

### 1. What do you need assistance with?
**Answer**: `API Access Request`

---

### 2. Your email address
**Answer**: `leslie@iabadvisors.com` (or your email)

---

### 3. Which role best describes your reason for requesting API access?
**Answer**: `I'm a developer`

---

### 4. What is your inquiry?
**Answer**: `I'm a developer and want to build a Reddit App that does not work in the Devvit ecosystem.`

---

### 5. Reddit account name
**Answer**: `[Your Reddit username]`

---

### 6. What benefit/purpose will the bot/app have for Redditors?

**Answer**:
```
This application analyzes public Reddit discussions to provide market sentiment insights for prediction markets on Polymarket. By aggregating and analyzing sentiment from relevant subreddits, it helps identify public opinion trends that may affect market outcomes. This provides value to traders and market participants by surfacing collective sentiment that may not be immediately apparent, contributing to more informed trading decisions in prediction markets.
```

---

### 7. Provide a detailed description of what the Bot/App will be doing on the Reddit platform.

**Answer**:
```
The application is an AI-powered trading bot for Polymarket prediction markets that performs sentiment analysis on Reddit discussions.

**Functionality:**
- Reads public posts and comments from specific subreddits (r/politics, r/worldnews, r/cryptocurrency, r/sports)
- Analyzes text content using NLP models (FinBERT) to extract sentiment scores
- Aggregates sentiment data to identify trends and patterns
- Combines Reddit sentiment with news articles and other data sources
- Uses this aggregated sentiment to inform trading decisions on prediction markets

**Technical Details:**
- Read-only access: The bot only reads public content, never posts, comments, or interacts with users
- Respects rate limits: Implements proper rate limiting and caching to stay within API limits
- Privacy-focused: Only analyzes publicly available content, no private data access
- Open source: Code is available on GitHub for transparency

**Use Case Example:**
If a prediction market asks "Will Bitcoin reach $100k by end of 2024?", the bot analyzes relevant Reddit discussions to gauge public sentiment, which is then combined with news sentiment and market data to make informed predictions.

The bot operates as a background service, continuously monitoring specified subreddits for relevant discussions and updating sentiment analysis in real-time.
```

---

### 8. What is missing from Devvit that prevents building on that platform?

**Answer**:
```
Devvit is designed for Reddit-specific applications and bots that run within Reddit's ecosystem and interact directly with Reddit's platform features. 

This application is an external trading bot that:
1. Needs to read Reddit data for external analysis and processing
2. Integrates Reddit data with multiple external data sources (news APIs, market data)
3. Performs complex NLP analysis using external ML models
4. Makes trading decisions on external platforms (Polymarket)
5. Requires continuous background operation independent of Reddit's infrastructure

These requirements are outside Devvit's scope, which is focused on Reddit-native applications. Our bot needs direct API access to read public content for external sentiment analysis and trading system integration.
```

---

### 9. Provide a link to source code or platform that will access the API.

**Answer**:
```
GitHub Repository: https://github.com/iabadvisors/ai-ml-trading-bot

(Or provide your actual repository URL if different)
```

---

### 10. What subreddits do you intend to use the bot/app in?

**Answer**:
```
r/politics, r/worldnews, r/cryptocurrency, r/sports
```

**Rationale**: These subreddits cover major topics that frequently appear in prediction markets - political events, world news, cryptocurrency discussions, and sports outcomes.

---

### 11. If applicable, what username will you be operating this bot/app under? (optional)

**Answer**: 
```
[Leave blank or provide if you have a specific Reddit account for the bot]
```

---

### 12. Attachments (optional)

**Answer**: 
```
[Optional: You can attach a screenshot of your application or architecture diagram if helpful]
```

---

## Additional Notes

- **Be honest and detailed**: Reddit values transparency about how their API will be used
- **Emphasize read-only access**: Make it clear you're only reading, not posting
- **Highlight compliance**: Mention that you'll respect rate limits and terms of service
- **Show value**: Explain how this benefits the Reddit community (even indirectly)

## After Submission

1. **Wait for response**: Reddit typically responds within a few days to a few weeks
2. **Check email**: They'll contact you at the email address you provided
3. **Be ready to answer follow-up questions**: They may ask for clarification
4. **Once approved**: You'll receive API credentials to add to your `.env` file

---

## Quick Copy-Paste Version

If you want to copy everything at once, here's a condensed version:

**Benefit**: "Analyzes public Reddit discussions to provide market sentiment insights for prediction markets, helping identify public opinion trends that affect market outcomes."

**Description**: "AI-powered trading bot for Polymarket that reads public posts from r/politics, r/worldnews, r/cryptocurrency, r/sports. Performs NLP sentiment analysis using FinBERT, aggregates sentiment data, and combines it with news/market data to inform trading decisions. Read-only access, respects rate limits, open source."

**Why not Devvit**: "External trading bot that needs to integrate Reddit data with external ML models and trading platforms, requiring continuous background operation outside Reddit's ecosystem."

**Subreddits**: "r/politics, r/worldnews, r/cryptocurrency, r/sports"

**Source**: "[Your GitHub repo URL]"

