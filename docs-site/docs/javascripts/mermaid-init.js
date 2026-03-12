function getMermaidThemeVariables(scheme) {
  var isDark = scheme === 'slate';
  if (isDark) {
    return {
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
      fontSize: '14px',
      lineColor: '#94A3B8',
      textColor: '#E2E8F0',
      primaryColor: '#172840',
      primaryTextColor: '#E2E8F0',
      primaryBorderColor: '#60A5FA',
      secondaryColor: '#102A2A',
      secondaryTextColor: '#E2E8F0',
      secondaryBorderColor: '#34D399',
      tertiaryColor: '#2A1B12',
      tertiaryTextColor: '#F1F5F9',
      tertiaryBorderColor: '#FB923C',
      noteBkgColor: '#111E30',
      noteBorderColor: '#334155',
      actorBkg: '#172840',
      actorBorder: '#60A5FA',
      actorTextColor: '#E2E8F0',
      labelBoxBkgColor: '#111E30',
      labelBoxBorderColor: '#334155',
    };
  }

  return {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
    fontSize: '14px',
    lineColor: '#475569',
    textColor: '#0F172A',
    primaryColor: '#EAF2FF',
    primaryTextColor: '#0F172A',
    primaryBorderColor: '#2563EB',
    secondaryColor: '#ECFDF5',
    secondaryTextColor: '#0F172A',
    secondaryBorderColor: '#059669',
    tertiaryColor: '#FFF7ED',
    tertiaryTextColor: '#0F172A',
    tertiaryBorderColor: '#EA580C',
    noteBkgColor: '#F8FAFC',
    noteBorderColor: '#CBD5E1',
    actorBkg: '#EAF2FF',
    actorBorder: '#1D4ED8',
    actorTextColor: '#0F172A',
    labelBoxBkgColor: '#F8FAFC',
    labelBoxBorderColor: '#CBD5E1',
  };
}

document$.subscribe(function () {
  if (typeof mermaid === 'undefined') {
    return;
  }

  var scheme = document.body.getAttribute('data-md-color-scheme') || 'default';
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: 'base',
    flowchart: {
      curve: 'linear',
      htmlLabels: true,
      useMaxWidth: true,
      nodeSpacing: 48,
      rankSpacing: 56,
      padding: 10,
    },
    sequence: {
      useMaxWidth: true,
      wrap: true,
      actorMargin: 52,
      boxMargin: 12,
      messageMargin: 32,
    },
    themeVariables: getMermaidThemeVariables(scheme),
  });

  mermaid.run({ querySelector: 'pre.mermaid' });
});
