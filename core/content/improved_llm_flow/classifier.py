from core.content.language_model_client import call_language_model
import json


async def classify_and_summarize(content: str):
    system_message = {
        "role": "system",
        "content": """You are a newsletter content expert. You specialize in categorizing content and then unpacking its value prop to promote the content based on why people find it valuable. Here are the types of newsletters you can choose from with examples and general thoughts on why readers find them valuable: "# Classifications

There are 7 types of newsletters:

- Briefs and bullets: headlines and brief summaries with one main top story (typically news or current events)
    - Example: Morning Brew:
    
    Drug stores locking up toothpaste is good for Amazon
    Lindsey Nicholson/Getty ImagesLindsey Nicholson/Getty Images
    Your local pharmacy locking up the toiletries is allowing Amazon to lock down new customers.
    
    Amazon CEO Andy Jassy said Thursday that brick-and-mortar drug stores taking extreme measures to thwart shoplifting have pushed customers to load up their online shopping carts because they don’t want to ask an employee to unlock a glass case.
    
    There’s evidence to back up Jassy’s belief that keeping merchandise under lock and key has hurt IRL stores:
    
    Hundreds of Walgreens, CVS, and Rite Aid locations have closed over the past few years, some of which coincides with when these retailers began believing that Danny Ocean and his crew were coming for their deodorant.
    In a Harris Poll from November 2023, 71% of shoppers said glass cases made them less likely to frequent a store. That figure was 89% among Gen Z respondents.
    In February 2023, Joe Budano, the CEO of anti-theft technology company Indyme, told Axios that the cases can cause sales to drop between 15% and 25%.
    Zoom out: Despite this sales bump for Amazon, its Q2 earnings, announced on Thursday, underwhelmed, and its outlook for Q3 fell short of market expectations. Amazon shares finished down 8.8% yesterday, since even if consumers don’t like pressing the button that calls for the pharmacy employee with the key, investors are still willing to hit the panic button.—DL
    
    - Value Prop: Easily digestible top stories. Summarize the main story in detail, highlighting key facts, figures, and quotes. For secondary stories, provide brief, punchy headlines.
- TLDR summaries: curates articles then links & summarizes them
    - Example: TLDR
    
    Science & Futuristic Technology
    Radioactive drugs strike cancer with precision (15 minute read)
    Radiation therapy has come a long way since X-ray therapy was born in 1896. Targeted radiopharmaceuticals helped the field achieve a new level of molecular precision. These agents deliver their radioactive payloads directly at tumor sites. While there are only a handful of these therapies commercially available for patients, the number is poised to grow as major players in the biopharmaceutical industry start to invest heavily in the technology.
    NASA indefinitely delays return of Starliner to review propulsion data (4 minute read)
    NASA has adjusted the date of the Starliner spacecraft's return to Earth to an unspecified time in July. The spacecraft was originally due to undock and return to Earth on June 14, but return opportunities have been waved off as more time is needed to review the data from the vehicle's problematic flight to the International Space Station. There were five separate leaks in the helium system that pressurizes Starliner's propulsion system and five of the vehicle's 28 reaction-control system thrusters failed as Starliner approached the station. NASA has not specified why it is not yet comfortable with releasing Starliner to fly back to Earth.
    
    - Value Prop: Collection of highly relevant resources in one place. Summarize each article's key points succinctly, maintaining the original order and structure.
- All bullets: super quick hitters on all of the necessary news (typically aimed for niche professional looking to skim and pick out the relevant info)
    - Example: Ben’s Bites
    
    NEWS
    Google Chrome to get 3 new AI features: Search with Google Lens on Desktop, Gemini-assisted lookup for browsing history and Tab Compare to judge products across multiple tabs.
    
    Microsoft adds OpenAI to its list of competitors in AI and search in its latest annual report.
    
    Websites are blocking the wrong AI scrapers (because AI companies keep making new ones).
    
    Google Cloud and YC partner to give startups a dedicated cluster of Nvidia GPUs.
    
    Suno and Udio are choosing offence in the copyright lawsuit by record labels.
    
    a16z is leading a $31M seed in Black Forest Labs, founders include OG Stable Diffusion creators.
    
    Speaking with two different AIs - One’s enthusiastic, another’s cautious.
    
    AI will fundamentally change sales workflows, with multimodal data and automation being key levers.
    
    Can an AI make a data-driven, visual story? One of the rare posts where the team gave AI a fair chance and judged its performance on various parts of the process.
    
    How to use Meta’s SAM 2 for video segmentation.
    
    View more →
    
    - Value Prop: Skimmable and targeted information. Create a list of the most important points, keeping each bullet brief and focused.
- Curated list: templated curation from the author (only valuable if from a thought leader)
    - Example: Sahil Bloom
    
    Question to make continuous progress:
    What are the boring, basic actions that you are avoiding right now?
    
    There's a Zen Buddhist saying that changed my life:
    
    "What do you do before enlightenment? Chop wood, carry water. What do you do after enlightenment? Chop wood, carry water."
    
    My interpretation: The internal state may change, but the external action never does.
    
    Every single day, chop wood, carry water.
    
    As you level up and grow, there's a tendency to lose sight of those boring basics that got you there in the first place.
    
    You feel the pull towards complexity (which is a trap!) and start looking for the new actions for the new you.
    
    But as the saying reminds us, you will change, but the actions needn't change with you.
    
    So, what are the boring, basic actions that you are avoiding right now?
    
    How can you chop wood and carry water today?
    
    - Value Prop: Expert-curated, more valuable than just resources. Summarize the expert's main points or recommendations, highlighting their unique insights.
- High-value curation: heavily-researched and data-intensive curation of targeted info (like sponsors for writers or investment opportunities)
    - Example: The Offer Sheet
    
    The Offer Sheet readers —
    
    Today, we’re thrilled to be sitting down with the Founder and CEO of Contractor+, Justin Smith.
    
    Contractor+ is setting out to change the future of the construction industry and they’ve already made quite a dent. Their platform makes it very simple for contractors to operate every part of their business from estimates to payment facilitation and team collaboration. They’re building AI to save contractors 20+ hours a week with their estimation and project management.
    
    I watched their intro video (below) and came away very impressed. Check out their video on Wefunder as well.
    
    Glad we were able to dive deeper with Justin and ask a few questions.
    
    Let’s Go!
    
    - Value prop: Hours of effort condensed into one resource for a very specific purpose. Focus on summarizing the key data points, trends, or opportunities identified by the curator.
- Daily analysis: daily analysis of an industry (from a field expert)
    - Example: Milk Road
    
    We’re focusing on Layer 2s and their tokens, exploring whether they are assets worth investing in right now. 🧐
    
    If L2s are a clear contender for the future of blockspace, shouldn't their tokens perform well?
    
    Well, if you have been paying attention to the charts, you might have noticed that L2 tokens look similar to the Terra Luna chart in 2022. 📉
    
    Ok ok, we are exaggerating, they aren’t THAT bad. But the last few months haven't been too nice to L2 tokens… 😅
    
    - Value prop: Continuing updates and interpretation from an expert. Summarize the main analysis or prediction, including key supporting evidence or data.
- Weekly deep dives: dive into a single topic
    - Example: Houck’s Newsletter
    
    Need a Friend(.com)?
    Hype Matters
    First — how could a founder possibly justify that domain expense so early on, especially when they have to also build hardware?
    
    Schiffmann understands that the bar for anyone to care about a consumer product that has a broad target market (lonely people) is incredibly high. It’s unlike launching a niche consumer product, or b2b product, where there are common threads you can easily pull on to get users excited.
    
    Layer on that it’s hardware that changes their day-to-day lives, and it takes real gravity to penetrate the cultural zeitgeist to the degree you need to, in order to have staying power.
    
    That’s why the production quality on the launch video is so high too.
    
    It’s a high-risk, high-reward moonshot launch — you have no choice but to go all-in.
    
    Could he have met that bar without owning [friend.com](http://friend.com/)? Maybe, but:
    
    We’re talking about it
    
    The price would’ve considerably gone up if he bought it post-launch
    
    He’s now going to raise a lot more money (more on that below)
    
    I suspect he “gets it” because of his previous viral launches around a COVID-19 tracker during the pandemic and an “Airbnb for Ukraine refugees” at the beginning of the current war.
    
    Last year I shared my 5-step playbook for how startups create hype.
    
    Schiffmann launched after already going through the first 4 stages and, if the product delivers on user expectations when it ships in Q1 of next year, has a legitimate shot of cracking the fifth as well.
    
    But there’s a long road between now and then.
    
    - Value prop: Highly researched single lesson. Provide a comprehensive summary of the main topic, including key arguments, data points, and conclusions. Return your response as a JSON string with 'classification' and 'summary' keys.""",
    }
    user_message = {
        "role": "user",
        "content": f"CUse your best judgement and reasoning abilities to classify this piece of content and tell what its value prop is: {content}. Knowing what readers find valuable about the piece, summarize it in the context of this value. In other words, ensure that your summary is really providing the value prop statement for each piece based on its actual contents. Imagine someone who fits the ideal reader profile for this newsletter, and consider what they would need to know if they didn't know about the newsletter. Don't leave out any important facts or quotes that you think make this a strong piece. Maintain the writer's original tone (funny vs. serious, etc), syntax, perspective, etc.",
    }
    response = await call_language_model(system_message, user_message)
    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # If we can't parse JSON, return a dictionary with default values
        return {"classification": "Unknown", "summary": response}
