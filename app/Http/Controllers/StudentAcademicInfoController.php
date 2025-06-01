<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\StudentAcademicInfo;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http; // ADD THIS LINE
use Illuminate\Support\Facades\Log;   // ADD THIS LINE

class StudentAcademicInfoController extends Controller
{
    /**
     * Display a listing of the resource.
     *
     * @return \Illuminate\Http\Response
     */
    public function index()
    {
        //
    }

    /**
     * Show the form for creating a new resource.
     *
     * @return \Illuminate\Http\Response
     */
    public function create()
    {
        //
    }

    /**
     * Store a newly created resource in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\Response
     */
    public function store(Request $request)
    {
        //
    }

    /**
     * Display the specified resource.
     *
     * @param  \App\Models\StudentAcademicInfo  $studentAcademicInfo
     * @return \Illuminate\Http\Response
     */
    public function show(StudentAcademicInfo $studentAcademicInfo)
    {
        //
    }

    /**
     * Show the form for editing the specified resource.
     *
     * @param  \App\Models\StudentAcademicInfo  $studentAcademicInfo
     * @return \Illuminate\Http\Response
     */
    public function edit(StudentAcademicInfo $studentAcademicInfo)
    {
        //
    }

    /**
     * Update the specified resource in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \App\Models\StudentAcademicInfo  $studentAcademicInfo
     * @return \Illuminate\Http\Response
     */
    public function update(Request $request, StudentAcademicInfo $studentAcademicInfo)
    {
        //
    }

    /**
     * Remove the specified resource from storage.
     *
     * @param  \App\Models\StudentAcademicInfo  $studentAcademicInfo
     * @return \Illuminate\Http\Response
     */
    public function destroy(StudentAcademicInfo $studentAcademicInfo)
    {
        //
    }

    // ADD THIS NEW METHOD TO YOUR CONTROLLER
    /**
     * Downloads the academic transcript for a given student ID from the microservice.
     *
     * @param string $studentId The ID of the student.
     * @return \Illuminate\Http\Response|\Illuminate\Http\RedirectResponse
     */
    public function downloadTranscript(string $studentId)
    {
        // The URL of your Python microservice within the Docker network.
        // 'transcript_microservice' is the Docker Compose service name defined in docker-compose.yml.
        // '5000' is the internal port the Flask app is listening on.
        $microserviceUrl = 'http://transcript_microservice:5000/transcript/' . $studentId;

        try {
            // Make an HTTP GET request to the microservice with a timeout.
            $response = Http::timeout(30)->get($microserviceUrl);

            // Check if the request was successful (HTTP status 2xx).
            if ($response->successful()) {
                $pdfContent = $response->body(); // Get the raw PDF content (binary data)

                // Set headers for PDF download.
                // 'Content-Type: application/pdf' tells the browser it's a PDF.
                // 'Content-Disposition: attachment; filename="..."' prompts the user to download the file.
                return response($pdfContent)
                        ->header('Content-Type', 'application/pdf')
                        ->header('Content-Disposition', 'attachment; filename="transcript_' . $studentId . '.pdf"');
            } else {
                // Handle HTTP errors returned by the microservice (e.g., 404 Not Found, 500 Internal Server Error).
                $statusCode = $response->status();
                // Attempt to get a more specific error message from the microservice's JSON response, if available.
                $errorMessage = $response->json()['description'] ?? 'An unknown error occurred.';
                Log::error("Microservice error for student {$studentId}: Status {$statusCode} - {$errorMessage}");
                return redirect()->back()->with('error', "Failed to generate transcript: {$errorMessage}");
            }
        } catch (\Illuminate\Http\Client\RequestException $e) {
            // Catch Guzzle HTTP client exceptions, such as connection refused, DNS resolution failure, or timeouts.
            Log::error("Microservice connection error for student {$studentId}: " . $e->getMessage());
            return redirect()->back()->with('error', 'Could not connect to the transcript service. Please try again later.');
        } catch (\Exception $e) {
            // Catch any other unexpected exceptions that might occur during the process.
            Log::error("Unexpected error calling transcript service for student {$studentId}: " . $e->getMessage());
            return redirect()->back()->with('error', 'An unexpected error occurred while generating the transcript.');
        }
    }
}