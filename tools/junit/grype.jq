# Converte a saida JSON do Grype em JUnit XML (um testcase com falha por vulnerabilidade).
"<?xml version=\"1.0\" encoding=\"UTF-8\"?><testsuites><testsuite name=\"grype\">"
+ ([.matches[] | "<testcase classname=\"" + (.artifact.name | @html) + " " + (.artifact.version | @html) + "\" name=\"" + .vulnerability.id + " [" + .vulnerability.severity + "]\"><failure type=\"" + .vulnerability.severity + "\" message=\"" + (.vulnerability.id | @html) + "\"/></testcase>"] | join(""))
+ "</testsuite></testsuites>"
