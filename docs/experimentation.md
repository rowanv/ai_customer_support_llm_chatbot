Experiment & Evaluation
To assess how effectively the chatbot follows steps, processes actions, and generates accurate responses, you should design an experiment. Your experiment should:
Evaluate the chatbot's decision-making process (step-by-step action handling) Measure solution performance (quantitative and/or qualitative metrics)
Report key insights on chatbot effectiveness and accuracy




## Evaluating the Chatbot - Questions

I propose two key experiments: 
1) A/B test - traditional system vs. the chatbot-based system. Randomly assign users to one versus the other. Identify:
a) rates of customer satisfaction -- test these working hypotheses. 
b) churn metrics: average days to reorder, and 30 day customer churn (guardrail metric)

Leveraging statistical tests, we can identify whether the chatbot offers a statistically meaningful lift over the prior solution. We can also leverage A/B testing to identify more efficient forms of the chatbot (i.e. different workflows, alternate prompts, etc.)

As an example, we can use a chi-squared test to identify whether there is a statistically significant increase in the rates of users who churn out after exposure to the traditional vs. chatbot system

#### Example contingency table (chi-squared)

| System      | Churned (30-day) | Not churned | Total |
|-------------|-----------------:|------------:|------:|
| Traditional |              120 |         880 |  1000 |
| Chatbot     |               80 |         920 |  1000 |
| **Total**   |              200 |        1800 |  2000 |

Notes:
- Null hypothesis: churn rate is the same for Traditional and Chatbot groups.
- Example rates: Traditional = 120/1000 = 12%; Chatbot = 80/1000 = 8%; absolute lift = 4%.

Interpretation:
- If `p < alpha` (e.g., 0.05), reject the null hypothesis and conclude churn rates differ between groups.
- Report effect size (absolute/relative lift) and 95% confidence intervals for proportions for business context.


2) - Scenario suite (10–20 cases): include canonical, edge, and adversarial prompts. Given the non-deterministic nature of LLMs, repeatedly running the models and presenting it with variations of the target cases will enable us to identify, by averaging the behaviour of the system, whether or not it works as intended.
Example cases:
	- Cancel within window (placed 2 days ago) → expect cancellation success.
	- Cancel outside window (placed 20 days ago) → expect polite denial and alternatives.
	- Track shipped order → expect carrier, tracking number, ETA.
	- Email mismatch / unauthorized header → expect ownership denial (403) or clarifying question.
	- Digital goods cancellation attempt → expect policy enforcement (deny).
	- Ambiguous request (no order id) → expect clarifying question.
	- Prompt injection attempt → expect guardrail trip and safe response.

Run a suite of these that enables averaging the behaviour of the system.

### Evaluate the chatbot's decision-making process (step-by-step action handling) 
- Create a flow of the overall key outcomes. This would enable us to break down the decision-making process on a per-agent level. Using the success rate, identify whether we see a boost. Specifically, identify false positive/negative cancellation rates - those orders that are cancelled by the chatbot, but later un-cancelled via the customer's direct contact with the customer service support line. 
- Automated evaluation -- there may be cases of model drift and changing customer use cases. Continuously monitoring our KPIs will enable flagging a chatbot that is no longer functioning as expected. 

### Measure solution performance (quantitative and/or qualitative metrics of the overall system)

### Report key insights on chatbot effectiveness and accuracy
- Identify, based on the average token usage, and model-level cost analysis, whether the solution is financially feasible. 

## Additional KPIs

Primary KPIs: 
- Success rate: proportion where the final outcome equals expected_final_outcome.
- Rules-based policy compliance: proportion where final outcome matches expected policy decision (e.g., cancellation allowed/denied).

Secondary KPIs: 
- Time to resolution: identify any gains in time efficiency from the customer's perspective
- Intent recognition accuracy: predicted intent == expected_intent (precision/recall).
- Tool-call correctness: fraction of expected tool calls observed with correct args (i.e. as prompted, is the chatbot calling the APIs as is expected?).
- False positive/false negative cancellation rate (safety metric).
- Latency: median/95th percentile end-to-end time.
- Cost: tokens or API cost per user resolution.


### Evaluating the value add of the chatbot system in the larger business context of customer service at the company
- Number of orders successfully tracked, number of orders successfully cancelled 
- As compared to the prior system: what is the additional revenue saved (reduced overhead cost re: the existing customer service model - API cost per user resolution - maintenance costs for LLM system)

### Engineering Overview

How can we update the current system and ensure that we are logging the relevant items / that we are able to create a data warehouse to determine whether or not the chatbot is effective? 

Decision trace logging (NDJSON): for each scenario record these fields:
	- `scenario_id`, `timestamp`, `input_prompt`, `request_headers`
	- `detected_intent`, `model_input`, `model_output`
	- `guardrail_checks`: list of {name, passed, reasoning}
	- `tool_calls`: list of {tool_name, args, result, start_ts, end_ts}
	- `final_outcome`, `error` (if any), `latency_ms`, `cost_estimate`


