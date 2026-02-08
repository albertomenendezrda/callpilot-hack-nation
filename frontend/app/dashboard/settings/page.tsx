'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Settings,
  Bell,
  Shield,
  Zap,
  Users
} from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="min-h-full flex flex-col bg-white">
      {/* Header: same height as sidebar (h-16) */}
      <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex items-center space-x-3">
          <Settings className="h-6 w-6 text-black" />
          <h1 className="text-2xl font-bold text-black">Settings</h1>
        </div>
      </div>

      {/* Main Content: scrollable */}
      <div className="flex-1 min-h-0 overflow-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* General Settings */}
        <Card className="border-2 border-black/10">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              General
            </CardTitle>
            <CardDescription>
              Configure general application settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Auto-refresh dashboard</p>
                <p className="text-sm text-black/60">Automatically refresh data every 5 seconds</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Enabled
              </Button>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Default search radius</p>
                <p className="text-sm text-black/60">Distance to search for providers</p>
              </div>
              <select className="px-3 py-2 border-2 border-black/10 rounded-md text-sm">
                <option>10 miles</option>
                <option>25 miles</option>
                <option>50 miles</option>
              </select>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-black">Maximum concurrent calls</p>
                <p className="text-sm text-black/60">How many providers to call simultaneously</p>
              </div>
              <select className="px-3 py-2 border-2 border-black/10 rounded-md text-sm">
                <option>15</option>
                <option>10</option>
                <option>5</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className="border-2 border-black/10">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              Notifications
            </CardTitle>
            <CardDescription>
              Configure how you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Email notifications</p>
                <p className="text-sm text-black/60">Receive updates via email</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Configure
              </Button>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">SMS notifications</p>
                <p className="text-sm text-black/60">Get text messages for important updates</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Configure
              </Button>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-black">Push notifications</p>
                <p className="text-sm text-black/60">Browser push notifications</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Configure
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* API & Integrations */}
        <Card className="border-2 border-black/10">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              API & Integrations
            </CardTitle>
            <CardDescription>
              Manage API connections and third-party integrations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Google Calendar</p>
                <p className="text-sm text-black/60">Sync appointments to your calendar</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Connect
              </Button>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Twilio</p>
                <p className="text-sm text-black/60">Phone calling infrastructure</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Connected
              </Button>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-black">ElevenLabs</p>
                <p className="text-sm text-black/60">AI voice agents</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Connected
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Account */}
        <Card className="border-2 border-black/10">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Account
            </CardTitle>
            <CardDescription>
              Manage your account settings and preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Profile information</p>
                <p className="text-sm text-black/60">Update your name and contact details</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Edit
              </Button>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-black/10">
              <div>
                <p className="font-medium text-black">Password</p>
                <p className="text-sm text-black/60">Change your password</p>
              </div>
              <Button variant="outline" size="sm" className="border-black/10">
                Change
              </Button>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-black">Delete account</p>
                <p className="text-sm text-black/60">Permanently delete your account and data</p>
              </div>
              <Button variant="outline" size="sm" className="border-red-200 text-red-600 hover:bg-red-50">
                Delete
              </Button>
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
