"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, X } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";

const plans = [
  {
    id: "free",
    name: "Free",
    price: "₹0",
    period: "forever",
    description: "Try out Dora with limited features",
    features: [
      "10 queries per day",
      "Basic drug interaction checks",
      "Email support",
      "Web access only",
    ],
    limitations: [
      "No offline access",
      "Limited citation depth",
      "No EMR integration",
      "No voice control",
    ],
  },
  {
    id: "professional",
    name: "Professional",
    price: "₹999",
    period: "per month",
    description: "Perfect for individual practitioners",
    features: [
      "Unlimited queries",
      "Advanced drug interaction database",
      "Full citation access",
      "Offline mode",
      "Desktop & mobile apps",
      "Voice control",
      "Priority email support",
      "EMR integration",
    ],
    popular: true,
  },
  {
    id: "institution",
    name: "Institution",
    price: "Custom",
    period: "contact sales",
    description: "For hospitals and large practices",
    features: [
      "Everything in Professional",
      "Multi-user accounts",
      "Admin dashboard",
      "Custom integrations",
      "Dedicated support",
      "Training & onboarding",
      "Custom knowledge base",
      "SLA guarantee",
    ],
  },
];

export default function PricingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "annual">("monthly");

  const handleSubscribe = (planId: string) => {
    if (!user) {
      router.push("/login");
      return;
    }

    // In production, this would initiate the payment flow
    console.log("Subscribe to:", planId);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-primary-50 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Select the perfect plan for your practice
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center bg-white dark:bg-gray-800 rounded-lg p-1 shadow">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`px-6 py-2 rounded-md transition-colors ${
                billingPeriod === "monthly"
                  ? "bg-primary text-white"
                  : "text-gray-600 dark:text-gray-400"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("annual")}
              className={`px-6 py-2 rounded-md transition-colors ${
                billingPeriod === "annual"
                  ? "bg-primary text-white"
                  : "text-gray-600 dark:text-gray-400"
              }`}
            >
              Annual
              <span className="ml-2 text-xs bg-green-500 text-white px-2 py-0.5 rounded">
                Save 20%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan) => (
            <Card
              key={plan.id}
              className={`relative ${
                plan.popular
                  ? "border-primary border-2 shadow-xl"
                  : ""
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-primary text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </span>
                </div>
              )}

              <CardHeader className="text-center pb-8 pt-8">
                <CardTitle className="text-2xl mb-2">{plan.name}</CardTitle>
                <div className="mb-2">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">
                    {plan.price}
                  </span>
                  {plan.price !== "Custom" && (
                    <span className="text-gray-500 ml-2">/{plan.period}</span>
                  )}
                </div>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                <ul className="space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {feature}
                      </span>
                    </li>
                  ))}
                  {plan.limitations?.map((limitation, idx) => (
                    <li key={`limit-${idx}`} className="flex items-start gap-2 opacity-50">
                      <X className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-500 line-through">
                        {limitation}
                      </span>
                    </li>
                  ))}
                </ul>

                <Button
                  className="w-full"
                  variant={plan.popular ? "default" : "outline"}
                  size="lg"
                  onClick={() => handleSubscribe(plan.id)}
                >
                  {plan.id === "free"
                    ? "Get Started Free"
                    : plan.id === "institution"
                    ? "Contact Sales"
                    : "Subscribe Now"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I switch plans later?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  Yes, you can upgrade or downgrade your plan at any time. Changes
                  will be reflected in your next billing cycle.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Is there a free trial?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  Yes, we offer a 14-day free trial of the Professional plan. No
                  credit card required.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">What payment methods do you accept?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  We accept all major credit/debit cards, UPI, net banking, and
                  institutional purchase orders.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Is my data secure?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  Absolutely. We are HIPAA compliant and use enterprise-grade
                  encryption. All patient data is processed locally and never
                  stored on our servers without explicit consent.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Have questions? We're here to help.
          </p>
          <Button variant="outline" size="lg">
            Contact Sales
          </Button>
        </div>
      </div>
    </div>
  );
}
