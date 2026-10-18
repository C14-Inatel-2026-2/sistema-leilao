# Converte a saida JSON do Grype em JUnit XML.
# So HIGH/CRITICAL viram <failure> — o mesmo criterio de --fail-on high do stage.
# Severidades menores entram como skipped para aparecer no relatorio sem marcar o build UNSTABLE.
(
  (.matches // [])
  | map(
      (.vulnerability.severity | ascii_downcase) as $sev
      | "<testcase classname=\"" + (.artifact.name | @html) + " " + (.artifact.version | @html)
        + "\" name=\"" + (.vulnerability.id | @html) + " [" + .vulnerability.severity + "]\">"
        + (if $sev == "high" or $sev == "critical"
           then "<failure type=\"" + .vulnerability.severity + "\" message=\"" + (.vulnerability.id | @html) + "\"/>"
           else "<skipped message=\"" + .vulnerability.severity + "\"/>"
           end)
        + "</testcase>"
    )
  | join("")
) as $cases
| ((.matches // []) | map(select((.vulnerability.severity | ascii_downcase) | . == "high" or . == "critical")) | length | tostring) as $failures
| ((.matches // []) | length | tostring) as $tests
| ((.matches // []) | map(select((.vulnerability.severity | ascii_downcase) | . != "high" and . != "critical")) | length | tostring) as $skipped
| "<?xml version=\"1.0\" encoding=\"UTF-8\"?><testsuites><testsuite name=\"grype\" tests=\"" + $tests + "\" failures=\"" + $failures + "\" skipped=\"" + $skipped + "\">"
  + $cases
  + "</testsuite></testsuites>"
