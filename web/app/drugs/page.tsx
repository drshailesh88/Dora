"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";
import { Pill, Plus, X, AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import type { DrugInteraction } from "@/types/api";

export default function DrugsPage() {
  const [drugs, setDrugs] = useState<string[]>([""]);
  const [patientMeds, setPatientMeds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [interactions, setInteractions] = useState<DrugInteraction[]>([]);
  const [error, setError] = useState("");

  const addDrug = () => {
    setDrugs([...drugs, ""]);
  };

  const removeDrug = (index: number) => {
    setDrugs(drugs.filter((_, i) => i !== index));
  };

  const updateDrug = (index: number, value: string) => {
    const newDrugs = [...drugs];
    newDrugs[index] = value;
    setDrugs(newDrugs);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setInteractions([]);

    const validDrugs = drugs.filter((d) => d.trim());
    if (validDrugs.length === 0) {
      setError("Please enter at least one drug");
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiClient.checkDrugInteractions(
        validDrugs,
        patientMeds.length > 0 ? patientMeds : undefined
      );

      if (response.success) {
        setInteractions(response.interactions);
      } else {
        setError(response.error || "Failed to check interactions");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to check interactions");
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "contraindicated":
        return "bg-red-100 text-red-800 border-red-200";
      case "major":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "moderate":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "minor":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getSeverityIcon = (severity: string) => {
    if (severity === "contraindicated" || severity === "major") {
      return <AlertTriangle className="h-5 w-5" />;
    }
    return <AlertTriangle className="h-5 w-5" />;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Drug Interaction Checker
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Check for drug-drug interactions and safety alerts
        </p>
      </div>

      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Enter Medications</CardTitle>
          <CardDescription>
            Add drugs to check for potential interactions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <Label>Drugs to Check</Label>
              {drugs.map((drug, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder="e.g., Aspirin, Metformin, Lisinopril"
                    value={drug}
                    onChange={(e) => updateDrug(index, e.target.value)}
                    disabled={isLoading}
                    className="flex-1"
                  />
                  {drugs.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => removeDrug(index)}
                      disabled={isLoading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={addDrug}
                disabled={isLoading}
                className="w-full"
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Another Drug
              </Button>
            </div>

            {error && (
              <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 p-3 rounded-md">
                {error}
              </div>
            )}

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking Interactions...
                </>
              ) : (
                <>
                  <Pill className="mr-2 h-4 w-4" />
                  Check Interactions
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {interactions.length === 0 && !isLoading && drugs.some((d) => d.trim()) && (
        <Card className="border-green-200 bg-green-50 dark:bg-green-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <div>
                <h3 className="font-semibold text-green-900 dark:text-green-100">
                  No Interactions Found
                </h3>
                <p className="text-sm text-green-700 dark:text-green-200">
                  No significant drug interactions detected for the entered medications.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {interactions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Interactions Found ({interactions.length})
          </h2>

          {interactions.map((interaction, idx) => (
            <Card
              key={idx}
              className={`border-2 ${getSeverityColor(interaction.severity)}`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(interaction.severity)}
                    <div>
                      <CardTitle className="text-lg">
                        {interaction.drug1} + {interaction.drug2}
                      </CardTitle>
                      <div className="mt-1">
                        <span
                          className={`inline-block px-2 py-1 text-xs font-semibold rounded uppercase ${getSeverityColor(
                            interaction.severity
                          )}`}
                        >
                          {interaction.severity}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Description</h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {interaction.description}
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Management</h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {interaction.management}
                  </p>
                </div>

                <div className="text-xs text-gray-500 pt-2 border-t">
                  Source: {interaction.source}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>About Drug Interaction Checking</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <p>
            This tool checks for known drug-drug interactions based on current
            medical databases and literature.
          </p>
          <p className="font-semibold text-gray-900 dark:text-gray-100">
            Severity Levels:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>
              <span className="font-medium">Contraindicated:</span> These drugs
              should not be used together
            </li>
            <li>
              <span className="font-medium">Major:</span> May cause serious
              adverse effects
            </li>
            <li>
              <span className="font-medium">Moderate:</span> May alter drug
              effectiveness or cause moderate effects
            </li>
            <li>
              <span className="font-medium">Minor:</span> Limited clinical
              significance
            </li>
          </ul>
          <p className="text-xs pt-2 border-t mt-4">
            Always consider patient-specific factors and consult current
            prescribing information. This tool is meant to assist, not replace,
            clinical judgment.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
