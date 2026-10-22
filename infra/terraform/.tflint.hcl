# TFLint's checks (CI's terraform job): the rules that come with Terraform's recommended preset,
# plus a type and a description on every variable and a description on every output.
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_typed_variables" {
  enabled = true
}
