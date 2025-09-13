/**
 * Comprehensive Test Framework for PRP Implementation
 * Tests research, validation, and cognitive synergy capabilities
 */

import { expect } from 'chai';
import { describe, it, beforeEach, afterEach } from 'mocha';
import { ResearchEngine } from '../src/engines/research.js';
import { ValidationEngineImpl } from '../src/engines/validation.js';
import { ContextManagerImpl } from '../src/managers/context.js';
import { CognitiveSynergyEngine } from '../examples/cognitive_synergy_integration.js';
import { GreptileClient } from '../src/clients/greptile.js';
import { Repository, QueryResponse } from '../src/types/index.js';

describe('PRP Framework - Comprehensive Testing Suite', () => {
  let researchEngine: ResearchEngine;
  let validationEngine: ValidationEngineImpl;
  let contextManager: ContextManagerImpl;
  let cognitiveSynergyEngine: CognitiveSynergyEngine;
  let mockGreptileClient: MockGreptileClient;

  beforeEach(async () => {
    // Initialize mock client
    mockGreptileClient = new MockGreptileClient();
    
    // Initialize engines
    researchEngine = new ResearchEngine(mockGreptileClient);
    validationEngine = new ValidationEngineImpl();
    contextManager = new ContextManagerImpl();
    cognitiveSynergyEngine = new CognitiveSynergyEngine(
      researchEngine,
      validationEngine,
      contextManager
    );
  });

  afterEach(async () => {
    // Cleanup
    mockGreptileClient.reset();
  });

  describe('Research Engine', () => {
    describe('Semantic Analysis', () => {
      it('should conduct comprehensive semantic analysis', async () => {
        const query = 'How is authentication implemented in this codebase?';
        const context = createMockResearchContext();
        
        const result = await researchEngine.conductSemanticAnalysis(query, context);
        
        expect(result).to.have.property('findings');
        expect(result).to.have.property('confidence');
        expect(result).to.have.property('completeness');
        expect(result).to.have.property('patterns');
        expect(result).to.have.property('recommendations');
        expect(result).to.have.property('followUpQueries');
        
        expect(result.findings).to.be.an('array');
        expect(result.confidence).to.be.a('number').and.be.within(0, 1);
        expect(result.completeness).to.be.a('number').and.be.within(0, 1);
        expect(result.patterns).to.be.an('array');
        expect(result.followUpQueries).to.be.an('array').with.length.greaterThan(0);
      });

      it('should generate intelligent follow-up queries', async () => {
        const mockResponse: QueryResponse = {
          message: 'Authentication is implemented using JWT tokens',
          sources: [
            {
              repository: 'test/repo',
              remote: 'github',
              branch: 'main',
              filepath: 'auth/jwt.ts',
              linestart: 1,
              lineend: 50,
              summary: 'JWT token implementation'
            }
          ]
        };
        
        const followUps = await researchEngine.generateFollowUpQueries(mockResponse);
        
        expect(followUps).to.be.an('array');
        expect(followUps.length).to.be.greaterThan(0);
        expect(followUps.length).to.be.lessThanOrEqual(10);
        
        // Should contain relevant follow-up questions
        const hasImplementationQuery = followUps.some(q => 
          q.toLowerCase().includes('implementation') || 
          q.toLowerCase().includes('example')
        );
        expect(hasImplementationQuery).to.be.true;
      });

      it('should validate information against multiple sources', async () => {
        const sources = [
          {
            repository: 'test/repo',
            remote: 'github',
            branch: 'main',
            filepath: 'auth/jwt.ts',
            linestart: 1,
            lineend: 50,
            summary: 'JWT implementation'
          },
          {
            repository: 'test/repo',
            remote: 'github',
            branch: 'main',
            filepath: 'auth/middleware.ts',
            linestart: 10,
            lineend: 30,
            summary: 'Auth middleware'
          }
        ];
        
        const context = {
          query: 'How is authentication implemented?',
          expectedAnswerType: 'implementation_details',
          domainContext: { primaryLanguages: ['typescript'], frameworks: ['express'], architecturalPatterns: ['mvc'], industryDomain: 'web_development' },
          qualityThreshold: 0.8
        };
        
        const result = await researchEngine.validateInformation(sources, context);
        
        expect(result).to.have.property('isValid');
        expect(result).to.have.property('confidence');
        expect(result).to.have.property('validationChecks');
        expect(result).to.have.property('issues');
        expect(result).to.have.property('suggestions');
        
        expect(result.confidence).to.be.a('number').and.be.within(0, 1);
        expect(result.validationChecks).to.be.an('array');
      });

      it('should build comprehensive knowledge graph', async () => {
        const repositories: Repository[] = [
          { remote: 'github', repository: 'test/repo1', branch: 'main' },
          { remote: 'github', repository: 'test/repo2', branch: 'main' }
        ];
        
        const knowledgeGraph = await researchEngine.buildKnowledgeGraph(repositories);
        
        expect(knowledgeGraph).to.have.property('nodes');
        expect(knowledgeGraph).to.have.property('edges');
        expect(knowledgeGraph).to.have.property('patterns');
        expect(knowledgeGraph).to.have.property('insights');
        expect(knowledgeGraph).to.have.property('lastUpdated');
        expect(knowledgeGraph).to.have.property('version');
        
        expect(knowledgeGraph.nodes).to.be.an('array');
        expect(knowledgeGraph.edges).to.be.an('array');
        expect(knowledgeGraph.patterns).to.be.an('array');
        expect(knowledgeGraph.insights).to.be.an('array');
      });

      it('should assess codebase health comprehensively', async () => {
        const repository: Repository = { remote: 'github', repository: 'test/repo', branch: 'main' };
        
        const healthMetrics = await researchEngine.assessCodebaseHealth(repository);
        
        expect(healthMetrics).to.have.property('technicalDebt');
        expect(healthMetrics).to.have.property('maintainability');
        expect(healthMetrics).to.have.property('testCoverage');
        expect(healthMetrics).to.have.property('performanceScore');
        expect(healthMetrics).to.have.property('securityScore');
        expect(healthMetrics).to.have.property('documentationQuality');
        expect(healthMetrics).to.have.property('overallHealth');
        expect(healthMetrics).to.have.property('recommendations');
        
        // All scores should be between 0 and 1
        expect(healthMetrics.technicalDebt).to.be.within(0, 1);
        expect(healthMetrics.maintainability).to.be.within(0, 1);
        expect(healthMetrics.testCoverage).to.be.within(0, 1);
        expect(healthMetrics.performanceScore).to.be.within(0, 1);
        expect(healthMetrics.securityScore).to.be.within(0, 1);
        expect(healthMetrics.documentationQuality).to.be.within(0, 1);
        expect(healthMetrics.overallHealth).to.be.within(0, 1);
        
        expect(healthMetrics.recommendations).to.be.an('array');
      });
    });

    describe('Pattern Recognition', () => {
      it('should identify architectural patterns', async () => {
        const codebaseSnapshot = createMockCodebaseSnapshot();
        const context = createMockResearchContext();
        
        const patterns = await researchEngine.identifyPatterns(codebaseSnapshot, context);
        
        expect(patterns).to.be.an('array');
        
        patterns.forEach(pattern => {
          expect(pattern).to.have.property('id');
          expect(pattern).to.have.property('name');
          expect(pattern).to.have.property('type');
          expect(pattern).to.have.property('description');
          expect(pattern).to.have.property('occurrences');
          expect(pattern).to.have.property('confidence');
          expect(pattern).to.have.property('benefits');
          expect(pattern).to.have.property('drawbacks');
          
          expect(pattern.confidence).to.be.within(0, 1);
          expect(pattern.occurrences).to.be.an('array');
        });
      });
    });
  });

  describe('Validation Engine', () => {
    describe('Response Validation', () => {
      it('should validate response comprehensively', async () => {
        const response: QueryResponse = {
          message: 'The authentication system uses JWT tokens with refresh token rotation',
          sources: [
            {
              repository: 'test/repo',
              remote: 'github',
              branch: 'main',
              filepath: 'auth/jwt.ts',
              linestart: 1,
              lineend: 50,
              summary: 'JWT implementation with refresh tokens'
            }
          ]
        };
        
        const originalQuery = 'How does the authentication system work?';
        
        const validation = await validationEngine.validateResponse(response, originalQuery);
        
        expect(validation).to.have.property('isValid');
        expect(validation).to.have.property('overallScore');
        expect(validation).to.have.property('confidence');
        expect(validation).to.have.property('validationChecks');
        expect(validation).to.have.property('qualityMetrics');
        expect(validation).to.have.property('inconsistencies');
        expect(validation).to.have.property('missingInformation');
        expect(validation).to.have.property('suggestedImprovements');
        
        expect(validation.overallScore).to.be.within(0, 1);
        expect(validation.confidence).to.be.within(0, 1);
        expect(validation.validationChecks).to.be.an('array').with.length(5); // 5 validation layers
        
        // Check validation check types
        const checkTypes = validation.validationChecks.map(check => check.type);
        expect(checkTypes).to.include('factual_accuracy');
        expect(checkTypes).to.include('completeness');
        expect(checkTypes).to.include('consistency');
        expect(checkTypes).to.include('relevance');
        expect(checkTypes).to.include('actionability');
      });

      it('should check consistency across multiple responses', async () => {
        const responses: QueryResponse[] = [
          {
            message: 'Authentication uses JWT tokens',
            sources: [{ repository: 'test/repo', remote: 'github', branch: 'main', filepath: 'auth/jwt.ts', linestart: 1, lineend: 20, summary: 'JWT tokens' }]
          },
          {
            message: 'JWT tokens are used for authentication with 24-hour expiry',
            sources: [{ repository: 'test/repo', remote: 'github', branch: 'main', filepath: 'auth/config.ts', linestart: 5, lineend: 15, summary: 'JWT config' }]
          }
        ];
        
        const consistencyReport = await validationEngine.checkConsistency(responses);
        
        expect(consistencyReport).to.have.property('overallConsistency');
        expect(consistencyReport).to.have.property('inconsistencies');
        expect(consistencyReport).to.have.property('consistentElements');
        expect(consistencyReport).to.have.property('recommendations');
        expect(consistencyReport).to.have.property('crossReferenceValidation');
        
        expect(consistencyReport.overallConsistency).to.be.within(0, 1);
        expect(consistencyReport.inconsistencies).to.be.an('array');
        expect(consistencyReport.consistentElements).to.be.an('array');
        expect(consistencyReport.crossReferenceValidation).to.be.an('array');
      });

      it('should assess response completeness', async () => {
        const response: QueryResponse = {
          message: 'Authentication is handled by JWT tokens',
          sources: [{ repository: 'test/repo', remote: 'github', branch: 'main', filepath: 'auth/jwt.ts', linestart: 1, lineend: 20, summary: 'JWT implementation' }]
        };
        
        const context = {
          originalQuery: 'How is authentication implemented, including security measures and error handling?',
          expectedAnswerType: 'comprehensive_implementation',
          domainContext: 'web_security',
          userIntent: 'understand_complete_system'
        };
        
        const completenessScore = await validationEngine.assessCompleteness(response, context);
        
        expect(completenessScore).to.have.property('score');
        expect(completenessScore).to.have.property('missingElements');
        expect(completenessScore).to.have.property('coverageAreas');
        expect(completenessScore).to.have.property('improvementSuggestions');
        expect(completenessScore).to.have.property('expectedVsActual');
        
        expect(completenessScore.score).to.be.within(0, 1);
        expect(completenessScore.missingElements).to.be.an('array');
        expect(completenessScore.coverageAreas).to.be.an('array');
      });

      it('should generate refinement suggestions', async () => {
        const validation = createMockValidationResult();
        
        const refinementPlan = await validationEngine.generateRefinementSuggestions(validation);
        
        expect(refinementPlan).to.have.property('refinementSteps');
        expect(refinementPlan).to.have.property('prioritizedImprovements');
        expect(refinementPlan).to.have.property('qualityTargets');
        expect(refinementPlan).to.have.property('estimatedImpact');
        expect(refinementPlan).to.have.property('implementationOrder');
        
        expect(refinementPlan.refinementSteps).to.be.an('array');
        expect(refinementPlan.prioritizedImprovements).to.be.an('array');
        expect(refinementPlan.qualityTargets).to.be.an('array');
        expect(refinementPlan.implementationOrder).to.be.an('array');
      });
    });

    describe('Quality Metrics', () => {
      it('should track validation metrics over time', async () => {
        // Simulate multiple validations
        for (let i = 0; i < 5; i++) {
          const mockResponse: QueryResponse = {
            message: `Test response ${i}`,
            sources: []
          };
          await validationEngine.validateResponse(mockResponse, `Test query ${i}`);
        }
        
        const metrics = await validationEngine.trackValidationMetrics();
        
        expect(metrics).to.have.property('totalValidations');
        expect(metrics).to.have.property('successRate');
        expect(metrics).to.have.property('averageConfidence');
        expect(metrics).to.have.property('commonIssues');
        expect(metrics).to.have.property('improvementTrends');
        expect(metrics).to.have.property('performanceMetrics');
        
        expect(metrics.totalValidations).to.equal(5);
        expect(metrics.successRate).to.be.within(0, 1);
        expect(metrics.averageConfidence).to.be.within(0, 1);
      });
    });
  });

  describe('Context Manager', () => {
    describe('Context Building', () => {
      it('should build comprehensive context layers', async () => {
        const session = createMockSessionContext();
        const repositories: Repository[] = [
          { remote: 'github', repository: 'test/repo', branch: 'main' }
        ];
        
        const contextStack = await contextManager.buildContextLayers(session, repositories);
        
        expect(contextStack).to.have.property('immediate');
        expect(contextStack).to.have.property('session');
        expect(contextStack).to.have.property('repository');
        expect(contextStack).to.have.property('domain');
        expect(contextStack).to.have.property('user');
        expect(contextStack).to.have.property('metadata');
        
        // Validate immediate context
        expect(contextStack.immediate).to.have.property('query');
        expect(contextStack.immediate).to.have.property('intent');
        expect(contextStack.immediate).to.have.property('expectedOutputType');
        expect(contextStack.immediate).to.have.property('urgency');
        expect(contextStack.immediate).to.have.property('scope');
        
        // Validate repository context
        expect(contextStack.repository).to.have.property('repositories');
        expect(contextStack.repository).to.have.property('architecturalPatterns');
        expect(contextStack.repository).to.have.property('technicalStack');
      });

      it('should compress context intelligently', async () => {
        const contextStack = await contextManager.buildContextLayers(
          createMockSessionContext(),
          [{ remote: 'github', repository: 'test/repo', branch: 'main' }]
        );
        
        const maxTokens = 500; // Small limit to force compression
        const compressed = await contextManager.compressContext(contextStack, maxTokens);
        
        expect(compressed).to.have.property('compressedStack');
        expect(compressed).to.have.property('compressionRatio');
        expect(compressed).to.have.property('preservedElements');
        expect(compressed).to.have.property('removedElements');
        expect(compressed).to.have.property('compressionStrategy');
        expect(compressed).to.have.property('qualityScore');
        
        expect(compressed.compressionRatio).to.be.within(0, 1);
        expect(compressed.qualityScore).to.be.within(0, 1);
        expect(compressed.preservedElements).to.be.an('array');
        expect(compressed.removedElements).to.be.an('array');
      });

      it('should retrieve relevant context for queries', async () => {
        const query = 'How is error handling implemented?';
        const contextStack = await contextManager.buildContextLayers(
          createMockSessionContext(),
          [{ remote: 'github', repository: 'test/repo', branch: 'main' }]
        );
        
        const relevantContext = await contextManager.retrieveRelevantContext(query, contextStack);
        
        expect(relevantContext).to.have.property('relevantElements');
        expect(relevantContext).to.have.property('relevanceScores');
        expect(relevantContext).to.have.property('contextSummary');
        expect(relevantContext).to.have.property('missingContext');
        expect(relevantContext).to.have.property('contextQuality');
        
        expect(relevantContext.relevantElements).to.be.an('array');
        expect(relevantContext.relevanceScores).to.be.instanceof(Map);
        expect(relevantContext.contextSummary).to.be.a('string');
        expect(relevantContext.contextQuality).to.be.within(0, 1);
      });

      it('should identify context patterns across sessions', async () => {
        const sessions = [
          createMockSessionContext('session1'),
          createMockSessionContext('session2'),
          createMockSessionContext('session3')
        ];
        
        const patterns = await contextManager.identifyContextPatterns(sessions);
        
        expect(patterns).to.be.an('array');
        
        patterns.forEach(pattern => {
          expect(pattern).to.have.property('id');
          expect(pattern).to.have.property('type');
          expect(pattern).to.have.property('pattern');
          expect(pattern).to.have.property('frequency');
          expect(pattern).to.have.property('contexts');
          expect(pattern).to.have.property('effectiveness');
          expect(pattern).to.have.property('recommendations');
          
          expect(pattern.frequency).to.be.a('number');
          expect(pattern.effectiveness).to.be.within(0, 1);
        });
      });
    });
  });

  describe('Cognitive Synergy Engine', () => {
    describe('Exponential Collaboration', () => {
      it('should create fusion zone with exponential capabilities', async () => {
        const humanInput = {
          query: 'Design a scalable authentication system',
          context: { domain: 'web_development', complexity: 'high' },
          preferences: { detailLevel: 'comprehensive', outputFormat: 'structured', interactionStyle: 'collaborative' },
          feedback: ['focus on security', 'include examples'],
          intent: 'implementation_planning'
        };
        
        const aiContext = {
          knowledgeBase: { patterns: [], bestPractices: [] },
          processingCapabilities: ['analysis', 'synthesis', 'validation'],
          availableTools: ['research', 'validation', 'context'],
          currentState: { session: 'active', quality: 0.8 }
        };
        
        const fusionResult = await cognitiveSynergyEngine.createFusionZone(humanInput, aiContext);
        
        expect(fusionResult).to.have.property('capabilities');
        expect(fusionResult).to.have.property('multiplier');
        expect(fusionResult).to.have.property('exponentialValue');
        expect(fusionResult).to.have.property('processingTime');
        expect(fusionResult).to.have.property('qualityScore');
        
        expect(fusionResult.multiplier).to.be.greaterThan(1);
        expect(fusionResult.exponentialValue).to.have.property('exponentialGain');
        expect(fusionResult.exponentialValue.exponentialGain).to.be.greaterThan(fusionResult.exponentialValue.baseValue);
        expect(fusionResult.qualityScore).to.be.within(0, 10);
      });

      it('should implement progressive enhancement loop', async () => {
        const initialRequest = 'Create a user management system';
        const context = {
          sessionId: 'test-session',
          userExperience: 'intermediate',
          domainContext: 'web_development',
          qualityRequirements: { accuracy: 0.9, completeness: 0.85, performance: 0.8 },
          timeConstraints: { maxProcessingTime: 30000, responseDeadline: new Date(), iterationLimit: 5 }
        };
        
        const progressiveResult = await cognitiveSynergyEngine.progressiveEnhancementLoop(
          initialRequest,
          context
        );
        
        expect(progressiveResult).to.have.property('versions');
        expect(progressiveResult).to.have.property('finalResult');
        expect(progressiveResult).to.have.property('evolutionMetrics');
        expect(progressiveResult).to.have.property('recommendations');
        
        expect(progressiveResult.versions).to.be.an('array').with.length(5);
        
        // Verify version progression
        const versions = progressiveResult.versions;
        expect(versions[0].version).to.equal('v0.1');
        expect(versions[1].version).to.equal('v0.2');
        expect(versions[2].version).to.equal('v0.3');
        expect(versions[3].version).to.equal('v0.4');
        expect(versions[4].version).to.equal('v0.5');
        
        expect(versions[0].description).to.include('Core functionality');
        expect(versions[4].description).to.include('Production-ready');
      });

      it('should perform bidirectional optimization', async () => {
        const initialQuery = 'Optimize database query performance';
        const context = {
          maxIterations: 3,
          qualityThreshold: 0.85,
          convergenceThreshold: 0.05,
          optimizationGoals: ['performance', 'maintainability', 'scalability']
        };
        
        const optimizationResult = await cognitiveSynergyEngine.bidirectionalOptimization(
          initialQuery,
          context
        );
        
        expect(optimizationResult).to.have.property('steps');
        expect(optimizationResult).to.have.property('finalResult');
        expect(optimizationResult).to.have.property('convergenceMetrics');
        expect(optimizationResult).to.have.property('extractedPatterns');
        
        expect(optimizationResult.steps).to.be.an('array');
        expect(optimizationResult.steps.length).to.be.lessThanOrEqual(context.maxIterations);
        
        // Verify optimization steps
        optimizationResult.steps.forEach((step, index) => {
          expect(step).to.have.property('iteration');
          expect(step).to.have.property('aiInterpretation');
          expect(step).to.have.property('humanRefinement');
          expect(step).to.have.property('implementation');
          expect(step).to.have.property('patterns');
          expect(step).to.have.property('qualityScore');
          
          expect(step.iteration).to.equal(index + 1);
          expect(step.qualityScore).to.be.within(0, 1);
        });
      });

      it('should build context accumulation stack', async () => {
        const sessionId = 'test-accumulation-session';
        const interactions = [
          { type: 'query', content: 'What is MVC pattern?', timestamp: new Date(), feedback: { rating: 4 } },
          { type: 'query', content: 'How to implement MVC in Express?', timestamp: new Date(), feedback: { rating: 5 } },
          { type: 'query', content: 'Best practices for MVC architecture?', timestamp: new Date(), feedback: { rating: 4 } }
        ];
        
        const accumulationResult = await cognitiveSynergyEngine.buildContextAccumulationStack(
          sessionId,
          interactions
        );
        
        expect(accumulationResult).to.have.property('finalContext');
        expect(accumulationResult).to.have.property('evolutionSteps');
        expect(accumulationResult).to.have.property('overallGrowth');
        expect(accumulationResult).to.have.property('knowledgeGraph');
        
        expect(accumulationResult.evolutionSteps).to.be.an('array').with.length(interactions.length);
        
        // Verify evolution steps
        accumulationResult.evolutionSteps.forEach((step, index) => {
          expect(step).to.have.property('interaction');
          expect(step).to.have.property('contextBefore');
          expect(step).to.have.property('contextAfter');
          expect(step).to.have.property('evolutionMetrics');
          expect(step).to.have.property('newPatterns');
          expect(step).to.have.property('clarityScore');
          expect(step).to.have.property('velocityMultiplier');
          
          expect(step.clarityScore).to.be.within(0, 1);
          expect(step.velocityMultiplier).to.be.greaterThanOrEqual(1);
        });
      });

      it('should optimize collaboration based on metrics', async () => {
        const metrics = {
          understanding: 0.7,  // Below threshold
          velocity: 3,         // Below threshold
          quality: 0.82,       // Above threshold
          reusability: 0.75,   // Below threshold
          exponentialGain: 2.5
        };
        
        const optimizationPlan = await cognitiveSynergyEngine.optimizeCollaboration(metrics);
        
        expect(optimizationPlan).to.have.property('optimizations');
        expect(optimizationPlan).to.have.property('expectedImprovement');
        expect(optimizationPlan).to.have.property('implementationPlan');
        expect(optimizationPlan).to.have.property('successMetrics');
        
        expect(optimizationPlan.optimizations).to.be.an('array');
        expect(optimizationPlan.expectedImprovement).to.be.a('number');
        
        // Should include optimizations for low metrics
        const optimizationActions = optimizationPlan.optimizations.map(opt => opt.action);
        expect(optimizationActions).to.include('clarify_objectives'); // understanding < 0.8
        expect(optimizationActions).to.include('change_approach');     // velocity < 5
        expect(optimizationActions).to.include('extract_patterns');    // reusability < 0.8
      });
    });
  });

  describe('Integration Tests', () => {
    it('should handle end-to-end research and validation workflow', async () => {
      const query = 'Analyze the security implementation in this authentication system';
      const repositories: Repository[] = [
        { remote: 'github', repository: 'test/secure-app', branch: 'main' }
      ];
      
      // Step 1: Research
      const researchContext = createMockResearchContext();
      researchContext.repositories = repositories;
      
      const analysisResult = await researchEngine.conductSemanticAnalysis(query, researchContext);
      
      // Step 2: Validate findings
      const mockResponse: QueryResponse = {
        message: analysisResult.findings[0]?.description || 'Security analysis complete',
        sources: analysisResult.sources
      };
      
      const validation = await validationEngine.validateResponse(mockResponse, query);
      
      // Step 3: Build context
      const session = createMockSessionContext();
      const contextStack = await contextManager.buildContextLayers(session, repositories);
      
      // Step 4: Cognitive synergy
      const humanInput = {
        query,
        context: { domain: 'security', complexity: 'high' },
        preferences: { detailLevel: 'comprehensive', outputFormat: 'structured', interactionStyle: 'analytical' },
        feedback: ['focus on vulnerabilities', 'include remediation'],
        intent: 'security_analysis'
      };
      
      const aiContext = {
        knowledgeBase: { patterns: analysisResult.patterns, bestPractices: [] },
        processingCapabilities: ['security_analysis', 'vulnerability_detection'],
        availableTools: ['research', 'validation', 'context'],
        currentState: { session: 'active', quality: validation.overallScore }
      };
      
      const fusionResult = await cognitiveSynergyEngine.createFusionZone(humanInput, aiContext);
      
      // Verify end-to-end flow
      expect(analysisResult.findings).to.be.an('array');
      expect(validation.isValid).to.be.a('boolean');
      expect(contextStack.repository.repositories).to.deep.equal(repositories);
      expect(fusionResult.exponentialValue.exponentialGain).to.be.greaterThan(1);
      
      // Verify quality improvements through the pipeline
      expect(fusionResult.qualityScore).to.be.greaterThanOrEqual(validation.overallScore);
    });
  });
});

// Mock implementations and helper functions

class MockGreptileClient extends GreptileClient {
  private responses: Map<string, QueryResponse> = new Map();
  
  constructor() {
    super({ apiKey: 'mock', githubToken: 'mock', baseUrl: 'mock' });
    this.setupMockResponses();
  }
  
  async queryRepositories(): Promise<QueryResponse> {
    return {
      message: 'Mock response from Greptile API',
      sources: [
        {
          repository: 'test/repo',
          remote: 'github',
          branch: 'main',
          filepath: 'src/auth.ts',
          linestart: 1,
          lineend: 50,
          summary: 'Authentication implementation'
        }
      ]
    };
  }
  
  async healthCheck(): Promise<boolean> {
    return true;
  }
  
  private setupMockResponses(): void {
    this.responses.set('authentication', {
      message: 'Authentication is implemented using JWT tokens with bcrypt for password hashing',
      sources: [
        {
          repository: 'test/repo',
          remote: 'github',
          branch: 'main',
          filepath: 'auth/jwt.ts',
          linestart: 1,
          lineend: 100,
          summary: 'JWT token implementation with refresh tokens'
        }
      ]
    });
  }
  
  reset(): void {
    this.responses.clear();
    this.setupMockResponses();
  }
}

function createMockResearchContext(): any {
  return {
    sessionId: 'test-session',
    repositories: [{ remote: 'github', repository: 'test/repo', branch: 'main' }],
    previousQueries: [],
    domainKnowledge: {
      primaryLanguages: ['typescript', 'javascript'],
      frameworks: ['express', 'react'],
      architecturalPatterns: ['mvc', 'microservices'],
      industryDomain: 'web_development'
    },
    userPreferences: {
      preferredDepth: 'deep' as const,
      focusAreas: ['security', 'performance'],
      outputFormat: 'detailed',
      includeExamples: true
    },
    confidenceThreshold: 0.8,
    researchDepth: 'comprehensive' as const,
    validationLevel: 'rigorous' as const
  };
}

function createMockCodebaseSnapshot(): any {
  return {
    files: [
      { path: 'src/auth.ts', type: 'typescript', size: 1000 },
      { path: 'src/user.ts', type: 'typescript', size: 800 },
      { path: 'src/middleware.ts', type: 'typescript', size: 500 }
    ],
    structure: {
      directories: ['src', 'test', 'config'],
      patterns: ['mvc', 'middleware']
    },
    dependencies: ['express', 'jsonwebtoken', 'bcrypt'],
    metrics: {
      complexity: 0.7,
      maintainability: 0.8,
      testCoverage: 0.75
    }
  };
}

function createMockValidationResult(): any {
  return {
    isValid: false,
    overallScore: 0.65,
    confidence: 0.8,
    validationChecks: [
      { type: 'factual_accuracy', score: 0.9, passed: true, details: {}, confidence: 0.9, recommendations: [] },
      { type: 'completeness', score: 0.5, passed: false, details: {}, confidence: 0.8, recommendations: ['Add error handling details'] },
      { type: 'consistency', score: 0.8, passed: true, details: {}, confidence: 0.85, recommendations: [] },
      { type: 'relevance', score: 0.7, passed: true, details: {}, confidence: 0.75, recommendations: [] },
      { type: 'actionability', score: 0.6, passed: false, details: {}, confidence: 0.7, recommendations: ['Include implementation steps'] }
    ],
    qualityMetrics: {
      accuracy: 0.9,
      completeness: 0.5,
      consistency: 0.8,
      relevance: 0.7,
      actionability: 0.6,
      overall: 0.65,
      breakdown: {
        strengths: ['factual_accuracy', 'consistency'],
        weaknesses: ['completeness', 'actionability'],
        improvements: ['relevance']
      }
    },
    inconsistencies: [],
    missingInformation: ['error handling', 'security considerations'],
    suggestedImprovements: [
      {
        id: 'imp1',
        type: 'completeness',
        description: 'Add comprehensive error handling information',
        priority: 0.8,
        estimatedImpact: 0.2,
        implementationComplexity: 0.6
      }
    ],
    validationSources: [],
    timestamp: new Date()
  };
}

function createMockSessionContext(sessionId: string = 'test-session'): any {
  return {
    session_id: sessionId,
    query_count: 3,
    exploration_domains: ['authentication', 'security', 'web_development'],
    depth_achieved: 0.7,
    patterns_discovered: ['jwt_pattern', 'middleware_pattern'],
    connections_made: ['auth_user_connection', 'security_middleware_connection'],
    created_at: Date.now() - 3600000, // 1 hour ago
    last_active: Date.now()
  };
}