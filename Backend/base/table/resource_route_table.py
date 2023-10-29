from base.route_converter import parse_route


class _FhirResourceRoute:
    rule = {}

    def __init__(self, route_file_path="./config/resource.route"):
        with open(route_file_path, newline='') as route_file:
            for line in route_file:
                line = line.split("#")[0]
                if "=" not in line:
                    continue

                result = self._handle_route(line.replace("\n", ""))
                if result["condition_name"] in self.rule.keys():
                    raise KeyError("Duplicate rule name in the resource.route.")
                self.rule[result["condition_name"]] = result

    @staticmethod
    def _handle_route(string) -> dict:
        route = {"condition_name": string.split("=")[0],
                 "resource_type": "=".join(string.split("=")[1:]).split(".")[0].capitalize(),
                 "methods": parse_route(".".join(string.split("=")[1].split(".")[1:]))
                 }
        return route

    def get_route_dict(self, resource_rule):
        """

        :param resource_rule: name of route
        :return: {
                  "condition_name": name of condition,
                  "resource_type": "Patient",
                  "methods": [
                    "get_age()"
                  ]
                }
        """
        if resource_rule not in self.rule:
            raise KeyError("Rule is not exist in the resource.route.")

        return self.rule[resource_rule]

    def get_route(self, resource_rule):
        """

        :param resource_rule: name of route
        :return: [
                "get_age()"
              ]
        """
        if resource_rule not in self.rule:
            raise KeyError("Rule is not exist in the resource.route.")

        return self.rule[resource_rule]["methods"]

    def get_rule_dict(self):
        return sorted(self.rule.keys())


if __name__ == "__main__":
    from route_converter import parse_route
    import json

    route_table = _FhirResourceRoute("../../config/resource.route")
    print(route_table.get_rule_dict())
    print(json.dumps(route_table.get_route_dict("lymph_invaded_amount"), indent=2))
