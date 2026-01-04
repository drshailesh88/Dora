"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BookOpen,
  Search,
  Zap,
  Shield,
  Download,
  Users,
  CheckCircle2,
  ArrowRight
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-primary-50 dark:from-gray-900 dark:to-gray-800">
      {/* Navigation */}
      <nav className="border-b bg-white/50 dark:bg-gray-900/50 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold text-primary">Dora</div>
          <div className="space-x-4">
            <Link href="/pricing">
              <Button variant="ghost">Pricing</Button>
            </Link>
            <Link href="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl md:text-7xl font-bold text-gray-900 dark:text-white mb-6">
          The Future of
          <span className="text-primary block mt-2">Medical Knowledge</span>
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
          Access evidence-based medical information instantly. Built for Indian doctors,
          powered by AI, trusted by healthcare professionals.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/register">
            <Button size="lg" className="text-lg px-8">
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button size="lg" variant="outline" className="text-lg px-8">
              View Pricing
            </Button>
          </Link>
        </div>
        <p className="text-sm text-gray-500 mt-4">
          14-day free trial. No credit card required.
        </p>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12">
          Why Doctors Love Dora
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <Card>
            <CardHeader>
              <Zap className="h-12 w-12 text-primary mb-4" />
              <CardTitle>Lightning Fast</CardTitle>
              <CardDescription>
                Get instant answers to medical queries with AI-powered search
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Download className="h-12 w-12 text-primary mb-4" />
              <CardTitle>Works Offline</CardTitle>
              <CardDescription>
                Access your medical knowledge base even without internet
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Shield className="h-12 w-12 text-primary mb-4" />
              <CardTitle>HIPAA Compliant</CardTitle>
              <CardDescription>
                Your patient data stays secure with enterprise-grade encryption
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <BookOpen className="h-12 w-12 text-primary mb-4" />
              <CardTitle>Evidence-Based</CardTitle>
              <CardDescription>
                Every answer backed by citations from peer-reviewed sources
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Search className="h-12 w-12 text-primary mb-4" />
              <CardTitle>Drug Interactions</CardTitle>
              <CardDescription>
                Check drug-drug interactions in real-time during prescription
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Users className="h-12 w-12 text-primary mb-4" />
              <CardTitle>EMR Integration</CardTitle>
              <CardDescription>
                Seamlessly integrates with DocAssist EMR and other systems
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Comparison */}
      <section className="bg-white dark:bg-gray-900 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">
            Dora vs. UpToDate
          </h2>
          <div className="max-w-4xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="text-2xl font-bold text-primary">Dora</h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>₹999/month (~$12/month)</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Works offline (critical for rural India)</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Native EMR integration</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Voice control with "Hey DocAssist"</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Patient context-aware answers</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Indian guidelines support</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-2xl font-bold text-gray-500">UpToDate</h3>
                <div className="space-y-3">
                  <div className="text-gray-500">$559/year</div>
                  <div className="text-gray-500">Cloud-only, no offline access</div>
                  <div className="text-gray-500">Third-party EMR integration only</div>
                  <div className="text-gray-500">No voice control</div>
                  <div className="text-gray-500">No patient context</div>
                  <div className="text-gray-500">Limited Indian guidelines</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-4xl font-bold mb-6">
          Join Thousands of Doctors
        </h2>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
          Start your 14-day free trial today. No credit card required.
        </p>
        <Link href="/register">
          <Button size="lg" className="text-lg px-8">
            Get Started Free
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white dark:bg-gray-900 py-8">
        <div className="container mx-auto px-4 text-center text-gray-600 dark:text-gray-400">
          <p>&copy; 2026 Dora by DocAssist. All rights reserved.</p>
          <div className="mt-4 space-x-4">
            <Link href="/privacy" className="hover:text-primary">
              Privacy Policy
            </Link>
            <Link href="/terms" className="hover:text-primary">
              Terms of Service
            </Link>
            <Link href="/contact" className="hover:text-primary">
              Contact
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
