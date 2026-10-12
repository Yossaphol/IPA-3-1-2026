provider "aws" {
  region     = "us-east-1"

  default_tags {
    tags = {
      Course    = "IPA-Terraform"
      ManagedBy = "Terraform"
    }
  }
}