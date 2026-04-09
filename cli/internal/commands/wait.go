package commands

import (
	"context"
	"fmt"
	"time"
)

// waitForCondition polls fn until it reports done or the context is cancelled.
func waitForCondition(ctx context.Context, interval time.Duration, fn func(context.Context) (bool, error)) error {
	if interval <= 0 {
		return fmt.Errorf("poll interval must be greater than zero")
	}

	done, err := fn(ctx)
	if err != nil || done {
		return err
	}

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			done, err := fn(ctx)
			if err != nil {
				return err
			}
			if done {
				return nil
			}
		}
	}
}
