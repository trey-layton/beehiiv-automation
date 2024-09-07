import asyncio
import os
import time
from dotenv import load_dotenv
from PIL import Image
from core.models.account_profile import AccountProfile
from core.content.image_generator import (
    generate_image_list_content,
    generate_image_list,
)

load_dotenv()

# Include the newsletter content directly in the script
NEWSLETTER_CONTENT = """
I'm Heartbroken...
Actions we can take, and a whole bunch of awesome resources!
Author
Bonnie Dilber
September 04, 2024


If you enjoy the free content each week, please take a second to click on the link and support our sponsors each week! It costs you nothing, but is a good way to support those who help keep this newsletter free!

Resources of the Week
Over 500 jobs on the job board here!

This post from Hailley Griffis who leads Communications and Content at Buffer has some top notch advice on what helped folks stand out in a a pool of 1500 applicants.

How public should you be on social media around your layoff? Check out some considerations here.

Workfolk launched a newsletter where they are highlighting various networking events and other opportunities in the startup space. I shared some tips for growing on LinkedIn as part of the first issue - check it out on LinkedIn!

I was heartbroken to hear about yet another school shooting…this time just about an hour outside of Atlanta where I grew up. Of course there’s a complex network of things that contribute to gun violence in this country including a lack of social safety nets, poverty, lack of mental health supports, etc. But the number one thing that separates the US from the rest of the world in this area is that we have more guns per capita than any other country.

We have politicians, most of whom have never stepped foot inside of a school, trying to “fix” education by banning books, preventing any sort of education or discussion rooted in DEI, fighting against teaching critical race theory, working to arm teachers in classrooms…anything but addressing the actual issues leading to unprecedented levels of gun violence.

Here’s a list of actions we can all take as citizens to combat gun violence courtesy of Sandy Hook Promise, and Everytown is also a great resource.

What might falling interest rates mean for the job market?!
You’ve probably heard that there’s a correlation between interest rates and job creation. Here’s a high level overview of how that works and what the upcoming drop in interest rates might mean for the market.

When interest rates fall, it’s cheaper to borrow money which fuels growth and expansion.

On top of that, there’s less incentive for companies or investors to keep cash on hand when interest rates are lower so it makes more sense for them to focus on investment as a way of expanding their wealth. This can help launch new startups as well who have struggled with raising capital.

People make bigger purchases that require loans when interest rates are lower which can spur job creation in fields like real estate, banking, construction, and the automotive industry.

So should we expect a big surge in the market?

Honestly, I still don’t think so. We’re seeing just a small drop and I suspect the powers that be will want to see how things shake out over the next few months with the economy and the election.

All that said, hopefully this will help us move in the right direction - the workforce deserves it!!

P.S. For those who are interested in more on how the job market might impact the election, here’s an analysis in Reuters based on Goldman Sachs and a fascinating look at how different scenarios may play out from Moody’s Analytics.


Decided to check out the cherry blossoms this week 🙂 

Secta is rolling out cool new backgrounds every week it seems! This week, I decided to give cherry blossoms a try - hopefully one day I’ll actually find myself among the cherry blossoms in Japan but until that day, thanks AI! Reminder that they offer us a community discount so if you need new headshots, check them out!

🙋Answering Your Questions🙋
Each week, I’ll answer one (or more!) of your questions in this section. You can submit your questions here.

How specific do recruiters and hiring managers actually want you to be during interviews? If I’m telling a story to highlight my work while answering a question, how much background context and detail should I give?

This is a tough balance because some will ask questions to get what they need and others won’t. Some prefer lots of details and may see higher level stories as vague, while others will call too much detail “rambling”. So this makes it tough for sure.

Personally, I think sharing a bit of context is important, but you don’t need to give them a play by play of how you got the situation. For example, “We realized we needed functionality that our existing CRM did not offer so I was charged with evaluating options, selecting, and driving the implementation of a new CRM” should be sufficient (vs. going into details of all the issues you were facing with the existing CRM.)

One thing you can do is frame up that you welcome questions. For example, you can say, “I’ll try to stay high level here, but I am happy to dive into more specifics around any of these areas” before you share the story, or you can say, “I know I gave just a quick overview, but let me know what specifics I can expand upon.” This increases the likelihood that they’ll dive in and get what they need if they didn’t!

For more resources to support you in your search, check out my Linktree.
My content is seen by over 8 million people each month. Need help getting the word out about your brand? Let’s connect!
"""


async def generate_outreach_image(
    newsletter_content: str, output_dir: str = "outreach_images"
):
    # Create a dummy AccountProfile (since we don't need a real one for this tool)
    dummy_profile = AccountProfile(
        account_id="outreach_tool",
        beehiiv_api_key="",
        subscribe_url="",
        publication_id="",
        custom_prompt="",
    )

    # Generate content
    content = await generate_image_list_content(newsletter_content, dummy_profile)

    # Generate image
    image = generate_image_list(content, save_locally=False)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save the image
    timestamp = int(time.time())
    img_path = os.path.join(output_dir, f"outreach_image_{timestamp}.jpg")
    image.save(img_path, "JPEG")

    print(f"Image saved: {img_path}")
    print("Generated content:")
    print(content)

    return img_path, content


async def main():
    print("PostOnce Outreach Image Generator")
    print("Generating image from the included newsletter content...")

    img_path, content = await generate_outreach_image(NEWSLETTER_CONTENT)
    print(f"\nImage generated and saved to: {img_path}")
    print("You can now send this image to the newsletter creator.")


if __name__ == "__main__":
    asyncio.run(main())
