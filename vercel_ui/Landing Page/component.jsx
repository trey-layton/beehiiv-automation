/**
 * v0 by Vercel.
 * @see https://v0.dev/t/65PrIA5Ekhf
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function Component() {
  return (
    <div className="flex flex-col min-h-[100dvh]">
      <header className="px-4 lg:px-6 h-14 flex items-center">
        <Link href="#" className="flex items-center justify-center" prefetch={false}>
          <img src="/placeholder.svg" width="24" height="24" alt="Acme Inc" className="h-6 w-6" />
          <span className="sr-only">Acme Inc</span>
        </Link>
        <nav className="ml-auto flex gap-4 sm:gap-6">
          <Link href="#" className="text-sm font-medium hover:underline underline-offset-4" prefetch={false}>
            Features
          </Link>
          <Link href="#" className="text-sm font-medium hover:underline underline-offset-4" prefetch={false}>
            Pricing
          </Link>
          <Link href="#" className="text-sm font-medium hover:underline underline-offset-4" prefetch={false}>
            About
          </Link>
          <Link href="#" className="text-sm font-medium hover:underline underline-offset-4" prefetch={false}>
            Contact
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        <section className="relative w-full bg-gradient-to-br from-primary to-secondary py-24 md:py-32 lg:py-40">
          <div className="container px-4 md:px-6">
            <div className="mx-auto max-w-3xl space-y-6 text-center">
              <h1 className="text-4xl font-bold tracking-tighter text-primary-foreground sm:text-5xl md:text-6xl lg:text-7xl">
                Transform Your Newsletter into Engaging Social Media Content in Minutes
              </h1>
              <p className="text-lg text-primary-foreground md:text-xl lg:text-2xl">
                AI-powered content repurposing for busy newsletter writers
              </p>
              <div>
                <Button
                  size="lg"
                  className="inline-flex items-center justify-center rounded-md px-8 py-3 text-sm font-medium transition-colors hover:bg-primary/80 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  Start Your Free Trial
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary to-secondary opacity-50 blur-3xl" />
            <div className="absolute inset-0 bg-[url('/newsletter-to-social.gif')] bg-cover bg-center bg-no-repeat opacity-20 animate-transform-content" />
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-primary to-secondary">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center text-primary-foreground">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">Key Benefits</h2>
                <p className="max-w-[900px] text-primary-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Our AI-powered content repurposing tool helps you transform your newsletter content into engaging
                  social media posts in just a few clicks.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <BoltIcon className="h-8 w-8" />
                  <h3 className="text-xl font-bold">Save Time</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">Cut content creation time by 90%</p>
                </div>
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <WandIcon className="h-8 w-8" />
                  <h3 className="text-xl font-bold">Boost Engagement</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">Consistent, platform-optimized posts</p>
                </div>
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <GaugeIcon className="h-8 w-8" />
                  <h3 className="text-xl font-bold">Grow Audience</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">Drive more newsletter subscriptions</p>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-primary to-secondary">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center text-primary-foreground">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">How It Works</h2>
                <p className="max-w-[900px] text-primary-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Our AI-powered content repurposing tool makes it easy to transform your newsletter content into
                  engaging social media posts.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <InboxIcon className="h-8 w-8" />
                  <h3 className="text-xl font-bold">Connect your newsletter</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">
                    Link your newsletter account and we'll analyze your content.
                  </p>
                </div>
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <WandIcon className="h-8 w-8" />
                  <h3 className="text-xl font-bold">Choose content types</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">
                    Select the social media platforms and post formats you want to create.
                  </p>
                </div>
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <GaugeIcon className="h-8 w-8" />
                  <h3 className="text-xl font-bold">Review and post</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">
                    Preview your content, make any adjustments, and schedule or publish directly.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-primary to-secondary">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center text-primary-foreground">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">Supported Platforms</h2>
                <p className="max-w-[900px] text-primary-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Transform your newsletter content into engaging posts for the platforms your audience uses.
                </p>
              </div>
              <div className="grid grid-cols-3 gap-6 sm:gap-8 md:gap-10">
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <img src="/placeholder.svg" width="48" height="48" alt="Twitter" className="w-12 h-12" />
                  <h3 className="text-xl font-bold">Twitter</h3>
                </div>
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <img src="/placeholder.svg" width="48" height="48" alt="LinkedIn" className="w-12 h-12" />
                  <h3 className="text-xl font-bold">LinkedIn</h3>
                </div>
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6 opacity-50 blur-sm">
                  <img src="/placeholder.svg" width="48" height="48" alt="Threads" className="w-12 h-12" />
                  <h3 className="text-xl font-bold">Threads</h3>
                  <p className="text-primary-foreground/80 text-center text-sm">Coming soon</p>
                </div>
              </div>
              <div className="mt-6">
                <Button
                  variant="outline"
                  className="inline-flex items-center justify-center rounded-md px-6 py-2 text-sm font-medium transition-colors hover:bg-primary/20 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 text-primary"
                >
                  Request other platforms
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-primary to-secondary">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center text-primary-foreground">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">Testimonials</h2>
                <p className="max-w-[900px] text-primary-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Hear what our customers have to say about our AI-powered content repurposing tool.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 justify-center">
                <div className="flex flex-col items-center justify-center space-y-2 rounded-md bg-primary/10 p-6">
                  <blockquote className="text-lg font-semibold leading-snug">
                    "I used to spend 4 hours researching, writing, then editing my newsletter. Then, I'd spend just as
                    much time going back through and picking out pieces that I wanted to then rewrite to fit each social
                    platform. Now, I do all of this in minutes, and it's better than if I'd tried to do it myself."
                  </blockquote>
                  <div>
                    <div className="font-semibold">Trey, Creator of The Startup Breakdown</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-primary to-secondary">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center text-primary-foreground">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">Pricing</h2>
                <p className="max-w-[900px] text-primary-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  7-Day Free Trial, No Credit Card Required
                </p>
                <p className="max-w-[900px] text-primary-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  $9.99/month after trial
                </p>
              </div>
              <div>
                <Button
                  size="lg"
                  className="inline-flex items-center justify-center rounded-md px-8 py-3 text-sm font-medium transition-colors hover:bg-primary/80 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  Start Your Free Trial
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-primary to-secondary">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center text-primary-foreground">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">
                  Ready to supercharge your social media presence?
                </h2>
                <Button
                  size="lg"
                  className="inline-flex items-center justify-center rounded-md px-8 py-3 text-sm font-medium transition-colors hover:bg-primary/80 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  Start Your Free Trial
                  <ArrowRightIcon className="ml-2 h-5 w-5" />
                </Button>
                <p className="text-primary-foreground/80 text-center text-sm">Contact us at laytontrey3@gmail.com</p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="flex flex-col gap-2 sm:flex" />
    </div>
  )
}

function ArrowRightIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  )
}


function BoltIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <circle cx="12" cy="12" r="4" />
    </svg>
  )
}


function GaugeIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12 14 4-4" />
      <path d="M3.34 19a10 10 0 1 1 17.32 0" />
    </svg>
  )
}


function InboxIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  )
}


function WandIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15 4V2" />
      <path d="M15 16v-2" />
      <path d="M8 9h2" />
      <path d="M20 9h2" />
      <path d="M17.8 11.8 19 13" />
      <path d="M15 9h0" />
      <path d="M17.8 6.2 19 5" />
      <path d="m3 21 9-9" />
      <path d="M12.2 6.2 11 5" />
    </svg>
  )
}


function XIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  )
}