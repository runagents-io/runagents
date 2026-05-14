package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// Client is an HTTP client for the RunAgents API.
type Client struct {
	endpoint   string
	apiKey     string
	httpClient *http.Client
}

// NewClient creates a new API client with the given endpoint and API key.
func NewClient(endpoint, apiKey string) *Client {
	return &Client{
		endpoint: normalizeEndpoint(endpoint),
		apiKey:   apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Get performs a GET request to the given path and returns the response body.
func (c *Client) Get(path string) ([]byte, error) {
	return c.GetWithQuery(path, nil)
}

// GetWithQuery performs a GET request to the given path and query values.
func (c *Client) GetWithQuery(path string, query url.Values) ([]byte, error) {
	req, err := c.newRequest(http.MethodGet, path, query, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	return c.do(req)
}

// Post performs a POST request with a JSON body and returns the response body.
func (c *Client) Post(path string, payload interface{}) ([]byte, error) {
	req, err := c.newRequest(http.MethodPost, path, nil, payload)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	return c.do(req)
}

// Patch performs a PATCH request with a JSON body and returns the response body.
func (c *Client) Patch(path string, payload interface{}) ([]byte, error) {
	req, err := c.newRequest(http.MethodPatch, path, nil, payload)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	return c.do(req)
}

// Put performs a PUT request with a JSON body and returns the response body.
func (c *Client) Put(path string, payload interface{}) ([]byte, error) {
	req, err := c.newRequest(http.MethodPut, path, nil, payload)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	return c.do(req)
}

// Delete performs a DELETE request to the given path.
func (c *Client) Delete(path string) error {
	req, err := c.newRequest(http.MethodDelete, path, nil, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}
	_, err = c.do(req)
	return err
}

func (c *Client) newRequest(method, path string, query url.Values, payload interface{}) (*http.Request, error) {
	target, err := c.buildURL(path, query)
	if err != nil {
		return nil, err
	}

	bodyReader, err := payloadReader(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(method, target, bodyReader)
	if err != nil {
		return nil, err
	}
	c.setHeaders(req)
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	return req, nil
}

func (c *Client) buildURL(path string, query url.Values) (string, error) {
	target, err := url.Parse(c.endpoint)
	if err != nil {
		return "", fmt.Errorf("invalid endpoint: %w", err)
	}
	normalizedPath := normalizePath(path)
	ref, err := url.Parse(normalizedPath)
	if err != nil {
		return "", fmt.Errorf("invalid path: %w", err)
	}
	if ref.IsAbs() {
		target = ref
	} else if ref.Path != "" {
		basePath := strings.TrimRight(target.Path, "/")
		target.Path = basePath + "/" + strings.TrimLeft(ref.Path, "/")
		target.RawQuery = ref.RawQuery
	}
	if len(query) > 0 {
		values := target.Query()
		for key, items := range query {
			for _, item := range items {
				values.Add(key, item)
			}
		}
		target.RawQuery = values.Encode()
	}
	return target.String(), nil
}

func payloadReader(payload interface{}) (io.Reader, error) {
	if payload == nil {
		return nil, nil
	}

	data, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request body: %w", err)
	}
	return bytes.NewReader(data), nil
}

func (c *Client) do(req *http.Request) ([]byte, error) {
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("API error (HTTP %d): %s", resp.StatusCode, string(body))
	}
	return body, nil
}

// setHeaders adds common headers to the request.
func (c *Client) setHeaders(req *http.Request) {
	if c.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+c.apiKey)
	}
}

func normalizeEndpoint(endpoint string) string {
	endpoint = strings.TrimRight(strings.TrimSpace(endpoint), "/")
	if endpoint == "" {
		return ""
	}
	u, err := url.Parse(endpoint)
	if err != nil || u.Scheme == "" || u.Host == "" {
		return endpoint
	}
	path := strings.TrimRight(u.Path, "/")
	switch {
	case path == "/api/v1" || strings.HasPrefix(path, "/api/v1/workspaces/"):
		u.Path = path
	case strings.HasPrefix(path, "/workspaces/"):
		u.Path = "/api/v1" + path
	default:
		u.Path = strings.TrimRight(path+"/api/v1", "/")
	}
	u.RawQuery = ""
	u.Fragment = ""
	return strings.TrimRight(u.String(), "/")
}

func normalizePath(path string) string {
	if strings.HasPrefix(path, "http://") || strings.HasPrefix(path, "https://") {
		return path
	}
	path = "/" + strings.TrimLeft(strings.TrimSpace(path), "/")
	if path == "/" {
		return ""
	}
	return path
}
