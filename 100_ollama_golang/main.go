package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

const localOllamaURL = "http://localhost:11434/api/chat"

type RequestPayload struct {
	Model  string `json:"model"`
	Prompt string `json:"prompt"`
}

type ResponsePayload struct {
	Completion string `json:"completion"`
}

func callLocalOllama(model, prompt string) (string, error) {
	payload := RequestPayload{
		Model:  model,
		Prompt: prompt,
	}
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("error marshalling payload: %w", err)
	}

	req, err := http.NewRequest("POST", localOllamaURL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return "", fmt.Errorf("error creating request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("error sending request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := ioutil.ReadAll(resp.Body)
		return "", fmt.Errorf("error response from server: %s", string(bodyBytes))
	}

	var responsePayload ResponsePayload
	if err := json.NewDecoder(resp.Body).Decode(&responsePayload); err != nil {
		return "", fmt.Errorf("error decoding response: %w", err)
	}

	return responsePayload.Completion, nil
}

func main() {
	model := "llama3.2" // Replace with the model you have installed in your local Ollama server.
	prompt := "What is the capital of France?"

	response, err := callLocalOllama(model, prompt)
	if err != nil {
		fmt.Printf("Error: %s\n", err)
		return
	}

	fmt.Printf("Ollama Response: %s\n", response)
}
