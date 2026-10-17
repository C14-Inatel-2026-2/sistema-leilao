# Converte a saida JSON do Hadolint em JUnit XML (um testcase com falha por achado).
"<?xml version=\"1.0\" encoding=\"UTF-8\"?><testsuites><testsuite name=\"hadolint\">"
+ ([.[] | "<testcase classname=\"Dockerfile\" name=\"" + .code + " (linha " + (.line | tostring) + ")\"><failure type=\"" + .level + "\" message=\"" + (.message | @html) + "\"/></testcase>"] | join(""))
+ "</testsuite></testsuites>"
