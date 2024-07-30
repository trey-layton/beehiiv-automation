/**
 * v0 by Vercel.
 * @see https://v0.dev/t/ZTButjMcs4l
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function Component() {
  return (
    <div className="flex flex-col items-center justify-center py-12 bg-background">
      <Card className="w-full max-w-md p-6 space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Let's get your newsletter connected</h1>
          <p className="text-muted-foreground">Enter your beehiiv API key to connect your newsletter.</p>
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-key">beehiiv API Key</Label>
            <Input id="api-key" placeholder="Enter your API key" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">How to do this</h3>
            <ol className="space-y-2 text-muted-foreground">
              <li>
                <span className="font-medium">1. Navigate to Settings from your beehiiv Dashboard,</span>
              </li>
              <li>
                <span className="font-medium">2. Click Integrations on the left hand navigation menu,</span>
              </li>
              <li>
                <span className="font-medium">3. Scroll down and select 'New API Key',</span>
              </li>
              <li>
                <span className="font-medium">4. Give it a name like 'PostOnce API Key' and click Create New Key,</span>
              </li>
              <li>
                <span className="font-medium">5. Copy this key and paste it in the field above.</span>
              </li>
            </ol>
          </div>
        </div>
        <div className="flex flex-col items-center">
          <Button>Connect Newsletter</Button>
          <div className="mt-4 text-sm text-muted-foreground">
            <Link href="#" className="hover:underline" prefetch={false}>
              Do this later
            </Link>
          </div>
        </div>
      </Card>
    </div>
  )
}