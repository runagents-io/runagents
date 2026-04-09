package commands

import (
	"os"

	"github.com/olekukonko/tablewriter"
)

func newTable(headers ...string) *tablewriter.Table {
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader(headers)
	table.SetBorder(false)
	table.SetAutoWrapText(false)
	return table
}
