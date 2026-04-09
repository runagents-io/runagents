package commands

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestWaitForConditionCompletes(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	attempts := 0
	err := waitForCondition(ctx, 10*time.Millisecond, func(context.Context) (bool, error) {
		attempts++
		return attempts >= 3, nil
	})
	if err != nil {
		t.Fatalf("expected success, got error: %v", err)
	}
	if attempts < 3 {
		t.Fatalf("expected at least 3 attempts, got %d", attempts)
	}
}

func TestWaitForConditionContextTimeout(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel()

	err := waitForCondition(ctx, 10*time.Millisecond, func(context.Context) (bool, error) {
		return false, nil
	})
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("expected deadline exceeded, got %v", err)
	}
}

func TestWaitForConditionRejectsInvalidInterval(t *testing.T) {
	err := waitForCondition(context.Background(), 0, func(context.Context) (bool, error) {
		return true, nil
	})
	if err == nil {
		t.Fatalf("expected interval validation error")
	}
}
