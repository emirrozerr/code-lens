import type {
  User,
  Repository,
  Domain,
  IndexingJob,
  Stats,
  GraphData,
  GraphNode,
  GraphEdge,
  ChatEvent,
} from '@/types/api';

// ─── Users ─────────────────────────────────────────────────────────────────

export const MOCK_USERS: User[] = [
  {
    id: 'u-001',
    email: 'admin@codelens.dev',
    role: 'admin',
    createdAt: '2025-11-01T09:00:00Z',
    lastLogin: '2026-05-17T08:22:14Z',
  },
  {
    id: 'u-002',
    email: 'user@codelens.dev',
    role: 'user',
    createdAt: '2026-01-15T14:30:00Z',
    lastLogin: '2026-05-16T16:45:00Z',
  },
];

// ─── Repositories ──────────────────────────────────────────────────────────

export const MOCK_REPOS: Repository[] = [
  {
    id: 'r-001',
    name: 'spring-petclinic',
    url: 'https://github.com/spring-projects/spring-petclinic',
    paths: ['src/main/java'],
    lastIndexed: '2026-05-17T07:45:00Z',
    nodeCount: 8431,
    status: 'indexed',
  },
  {
    id: 'r-002',
    name: 'spring-boot-realworld',
    url: 'https://github.com/gothinkster/spring-boot-realworld-example-app',
    paths: ['src/main/java'],
    lastIndexed: '2026-05-16T23:12:00Z',
    nodeCount: 4218,
    status: 'indexed',
  },
  {
    id: 'r-003',
    name: 'django-ecommerce',
    url: 'https://github.com/example/django-ecommerce',
    paths: ['apps', 'core'],
    lastIndexed: '2026-05-15T11:30:00Z',
    nodeCount: 2174,
    status: 'failed',
  },
];

// ─── Domains ───────────────────────────────────────────────────────────────

export const MOCK_DOMAINS: Domain[] = [
  {
    id: 'd-001',
    name: 'Pet Management',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 34,
    summary:
      'Handles CRUD operations for pets, including pet types and owner associations. Central to the clinic\'s data model — Pet, PetType, and PetValidator form the core, with PetRepository providing JPA persistence.',
    humanVerified: true,
    lastUpdated: '2026-05-14T10:00:00Z',
  },
  {
    id: 'd-002',
    name: 'Veterinary Services',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 28,
    summary:
      'Manages veterinarians, their specialties, and visit records. VetService orchestrates scheduling while VisitRepository ensures durable persistence of all clinical encounters.',
    humanVerified: true,
    lastUpdated: '2026-05-14T10:05:00Z',
  },
  {
    id: 'd-003',
    name: 'Owner Management',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 22,
    summary:
      'Responsible for owner registration, profile updates, and search. OwnerController exposes REST endpoints; OwnerRepository extends JpaRepository with custom JPQL for name-based lookup.',
    humanVerified: false,
    lastUpdated: '2026-05-15T09:20:00Z',
  },
  {
    id: 'd-004',
    name: 'Appointment Scheduling',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 19,
    summary:
      'Coordinates visit bookings between owners, pets, and vets. Validates availability constraints and emits scheduling events consumed downstream by the notification domain.',
    humanVerified: false,
    lastUpdated: '2026-05-15T09:25:00Z',
  },
  {
    id: 'd-005',
    name: 'Data Access Layer',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 31,
    summary:
      'Spring Data JPA repositories and entity base classes. Provides consistent transaction management and connection pooling via HikariCP configuration.',
    humanVerified: true,
    lastUpdated: '2026-05-13T16:00:00Z',
  },
  {
    id: 'd-006',
    name: 'REST Controllers',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 26,
    summary:
      'MVC controller layer exposing the clinic\'s HTTP API. Each controller delegates to a corresponding service; error handling is centralized in GlobalExceptionHandler.',
    humanVerified: true,
    lastUpdated: '2026-05-13T16:05:00Z',
  },
  {
    id: 'd-007',
    name: 'Configuration & Setup',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 14,
    summary:
      'Application configuration beans, security setup, and Spring Boot auto-configuration overrides. WebMvcConfig, SecurityConfig, and cache configuration live here.',
    humanVerified: false,
    lastUpdated: '2026-05-15T09:30:00Z',
  },
  {
    id: 'd-008',
    name: 'Shared Utilities',
    repoId: 'r-001',
    repoName: 'spring-petclinic',
    memberCount: 11,
    summary:
      'Cross-cutting utility classes — date formatters, validation helpers, and the BaseEntity hierarchy shared across all JPA entities.',
    humanVerified: false,
    lastUpdated: '2026-05-15T09:35:00Z',
  },
  {
    id: 'd-009',
    name: 'Article Management',
    repoId: 'r-002',
    repoName: 'spring-boot-realworld',
    memberCount: 41,
    summary:
      'Full lifecycle management for articles: creation, tagging, favoriting, and comment threads. ArticleService coordinates with TagRepository and CommentRepository for composite operations.',
    humanVerified: true,
    lastUpdated: '2026-05-16T11:00:00Z',
  },
  {
    id: 'd-010',
    name: 'User Profile',
    repoId: 'r-002',
    repoName: 'spring-boot-realworld',
    memberCount: 29,
    summary:
      'User registration, profile reads, and follower/following graph management. ProfileService enforces self-follow prevention and handles the bidirectional follower relationship.',
    humanVerified: true,
    lastUpdated: '2026-05-16T11:05:00Z',
  },
  {
    id: 'd-011',
    name: 'Authentication',
    repoId: 'r-002',
    repoName: 'spring-boot-realworld',
    memberCount: 23,
    summary:
      'JWT generation and validation for the realworld API. JwtTokenFilter inspects every request; JwtTokenProvider signs and verifies tokens against the configured secret.',
    humanVerified: true,
    lastUpdated: '2026-05-16T11:10:00Z',
  },
  {
    id: 'd-012',
    name: 'Product Catalog',
    repoId: 'r-003',
    repoName: 'django-ecommerce',
    memberCount: 38,
    summary:
      'Django models and views for product listing, category trees, and inventory tracking. ProductManager provides the custom queryset logic for availability filtering.',
    humanVerified: false,
    lastUpdated: '2026-05-15T11:30:00Z',
  },
];

// ─── Indexing Jobs ─────────────────────────────────────────────────────────

function makeJob(
  index: number,
  repoId: string,
  repoName: string,
  status: 'succeeded' | 'running' | 'failed' | 'pending',
  hoursAgo: number,
): IndexingJob {
  const startedAt = new Date(Date.now() - hoursAgo * 3_600_000).toISOString();
  const succeeded = status === 'succeeded';
  const failed = status === 'failed';
  const durationMs = succeeded ? 12000 + index * 800 : failed ? 4000 + index * 200 : null;
  return {
    id: `j-${String(index).padStart(3, '0')}`,
    repoId,
    repoName,
    status,
    startedAt,
    finishedAt:
      succeeded || failed
        ? new Date(new Date(startedAt).getTime() + (durationMs ?? 0)).toISOString()
        : null,
    durationMs,
    nodeCount: succeeded ? 8431 - index * 12 : null,
    error:
      status === 'failed'
        ? 'Neo4j connection timeout after 30s. Retrying next scheduled run.'
        : null,
  };
}

export const MOCK_JOBS: IndexingJob[] = [
  makeJob(1, 'r-001', 'spring-petclinic', 'succeeded', 0.5),
  makeJob(2, 'r-002', 'spring-boot-realworld', 'running', 0.1),
  makeJob(3, 'r-003', 'django-ecommerce', 'failed', 2),
  makeJob(4, 'r-001', 'spring-petclinic', 'succeeded', 24),
  makeJob(5, 'r-002', 'spring-boot-realworld', 'succeeded', 25),
  makeJob(6, 'r-001', 'spring-petclinic', 'succeeded', 48),
  makeJob(7, 'r-003', 'django-ecommerce', 'failed', 49),
  makeJob(8, 'r-002', 'spring-boot-realworld', 'succeeded', 72),
  makeJob(9, 'r-001', 'spring-petclinic', 'succeeded', 96),
  makeJob(10, 'r-002', 'spring-boot-realworld', 'succeeded', 97),
  makeJob(11, 'r-001', 'spring-petclinic', 'failed', 120),
  makeJob(12, 'r-003', 'django-ecommerce', 'pending', 0.01),
  makeJob(13, 'r-001', 'spring-petclinic', 'succeeded', 144),
  makeJob(14, 'r-002', 'spring-boot-realworld', 'succeeded', 145),
  makeJob(15, 'r-003', 'django-ecommerce', 'failed', 168),
  makeJob(16, 'r-001', 'spring-petclinic', 'succeeded', 192),
  makeJob(17, 'r-002', 'spring-boot-realworld', 'succeeded', 193),
  makeJob(18, 'r-001', 'spring-petclinic', 'succeeded', 216),
  makeJob(19, 'r-003', 'django-ecommerce', 'succeeded', 217),
  makeJob(20, 'r-001', 'spring-petclinic', 'succeeded', 240),
  makeJob(21, 'r-002', 'spring-boot-realworld', 'succeeded', 241),
  makeJob(22, 'r-001', 'spring-petclinic', 'succeeded', 264),
  makeJob(23, 'r-003', 'django-ecommerce', 'failed', 265),
  makeJob(24, 'r-002', 'spring-boot-realworld', 'succeeded', 288),
  makeJob(25, 'r-001', 'spring-petclinic', 'succeeded', 312),
  makeJob(26, 'r-002', 'spring-boot-realworld', 'succeeded', 313),
  makeJob(27, 'r-003', 'django-ecommerce', 'pending', 0.02),
  makeJob(28, 'r-001', 'spring-petclinic', 'succeeded', 336),
  makeJob(29, 'r-002', 'spring-boot-realworld', 'succeeded', 337),
  makeJob(30, 'r-001', 'spring-petclinic', 'succeeded', 360),
  makeJob(31, 'r-003', 'django-ecommerce', 'failed', 361),
  makeJob(32, 'r-002', 'spring-boot-realworld', 'succeeded', 384),
  makeJob(33, 'r-001', 'spring-petclinic', 'succeeded', 408),
  makeJob(34, 'r-002', 'spring-boot-realworld', 'succeeded', 409),
  makeJob(35, 'r-001', 'spring-petclinic', 'succeeded', 432),
  makeJob(36, 'r-003', 'django-ecommerce', 'succeeded', 433),
  makeJob(37, 'r-001', 'spring-petclinic', 'succeeded', 456),
  makeJob(38, 'r-002', 'spring-boot-realworld', 'succeeded', 457),
  makeJob(39, 'r-003', 'django-ecommerce', 'failed', 480),
  makeJob(40, 'r-001', 'spring-petclinic', 'succeeded', 504),
  makeJob(41, 'r-002', 'spring-boot-realworld', 'succeeded', 505),
  makeJob(42, 'r-001', 'spring-petclinic', 'succeeded', 528),
  makeJob(43, 'r-003', 'django-ecommerce', 'pending', 0.03),
  makeJob(44, 'r-002', 'spring-boot-realworld', 'succeeded', 552),
  makeJob(45, 'r-001', 'spring-petclinic', 'succeeded', 576),
  makeJob(46, 'r-002', 'spring-boot-realworld', 'succeeded', 577),
  makeJob(47, 'r-003', 'django-ecommerce', 'failed', 600),
  makeJob(48, 'r-001', 'spring-petclinic', 'succeeded', 624),
  makeJob(49, 'r-002', 'spring-boot-realworld', 'succeeded', 625),
  makeJob(50, 'r-001', 'spring-petclinic', 'succeeded', 648),
];

// ─── Stats ─────────────────────────────────────────────────────────────────

export const MOCK_STATS: Stats = {
  reposCount: MOCK_REPOS.length,
  totalNodes: MOCK_REPOS.reduce((sum, r) => sum + r.nodeCount, 0),
  domainsCount: MOCK_DOMAINS.length,
  activeUsers: MOCK_USERS.length,
  neo4jStatus: 'ok',
  mcpUptime: 99.92,
  lastSuccessfulIndex: MOCK_JOBS.find((j) => j.status === 'succeeded')?.finishedAt ?? null,
};

// ─── Graph data ────────────────────────────────────────────────────────────

// Node templates per domain: [label, file, signature]
const NODE_TEMPLATES: Record<string, [string, string, string][]> = {
  'd-001': [
    ['Pet', 'model/Pet.java', 'class Pet extends NamedEntity'],
    ['PetType', 'model/PetType.java', 'class PetType extends NamedEntity'],
    ['PetController', 'web/PetController.java', 'class PetController'],
    ['PetRepository', 'repository/PetRepository.java', 'interface PetRepository extends JpaRepository<Pet, Integer>'],
    ['PetService', 'service/PetService.java', 'class PetService'],
    ['PetValidator', 'web/PetValidator.java', 'class PetValidator implements Validator'],
    ['PetTypeFormatter', 'web/PetTypeFormatter.java', 'class PetTypeFormatter implements Formatter<PetType>'],
    ['savePet', 'web/PetController.java', 'void savePet(Pet pet, BindingResult result)'],
    ['findPetTypes', 'repository/PetRepository.java', 'List<PetType> findPetTypes()'],
    ['processCreationForm', 'web/PetController.java', 'String processCreationForm(Owner owner, Pet pet)'],
    ['validate', 'web/PetValidator.java', 'void validate(Object obj, Errors errors)'],
    ['parse', 'web/PetTypeFormatter.java', 'PetType parse(String text, Locale locale)'],
    ['findById', 'repository/PetRepository.java', 'Pet findById(int id)'],
    ['save', 'service/PetService.java', 'void save(Pet pet)'],
    ['findPetById', 'service/PetService.java', 'Pet findPetById(int id)'],
    ['initOwnerBinder', 'web/PetController.java', 'void initOwnerBinder(WebDataBinder dataBinder)'],
    ['PetTypeRepository', 'repository/PetTypeRepository.java', 'interface PetTypeRepository extends JpaRepository<PetType, Integer>'],
    ['getAllPetTypes', 'service/PetService.java', 'List<PetType> getAllPetTypes()'],
    ['initCreationForm', 'web/PetController.java', 'String initCreationForm(Owner owner, ModelMap model)'],
    ['processUpdateForm', 'web/PetController.java', 'String processUpdateForm(Pet pet, BindingResult result)'],
  ],
  'd-002': [
    ['Vet', 'model/Vet.java', 'class Vet extends Person'],
    ['Specialty', 'model/Specialty.java', 'class Specialty extends NamedEntity'],
    ['VetController', 'web/VetController.java', 'class VetController'],
    ['VetRepository', 'repository/VetRepository.java', 'interface VetRepository extends JpaRepository<Vet, Integer>'],
    ['VetService', 'service/VetService.java', 'class VetService'],
    ['Visit', 'model/Visit.java', 'class Visit extends BaseEntity'],
    ['VisitController', 'web/VisitController.java', 'class VisitController'],
    ['VisitRepository', 'repository/VisitRepository.java', 'interface VisitRepository extends JpaRepository<Visit, Integer>'],
    ['Vets', 'model/Vets.java', 'class Vets'],
    ['showVetList', 'web/VetController.java', 'String showVetList(Model model)'],
    ['findAll', 'repository/VetRepository.java', 'Collection<Vet> findAll()'],
    ['findByPetId', 'repository/VisitRepository.java', 'List<Visit> findByPetId(int petId)'],
    ['saveVisit', 'service/VetService.java', 'void saveVisit(Visit visit)'],
    ['processNewVisitForm', 'web/VisitController.java', 'String processNewVisitForm(Visit visit)'],
    ['showVetsJson', 'web/VetController.java', 'Vets showVetsJson()'],
    ['initNewVisitForm', 'web/VisitController.java', 'String initNewVisitForm(Pet pet, Model model)'],
    ['getVisitsByPetId', 'service/VetService.java', 'List<Visit> getVisitsByPetId(int petId)'],
    ['getSpecialties', 'model/Vet.java', 'Set<Specialty> getSpecialties()'],
    ['addSpecialty', 'model/Vet.java', 'void addSpecialty(Specialty specialty)'],
  ],
  'd-003': [
    ['Owner', 'model/Owner.java', 'class Owner extends Person'],
    ['OwnerController', 'web/OwnerController.java', 'class OwnerController'],
    ['OwnerRepository', 'repository/OwnerRepository.java', 'interface OwnerRepository extends JpaRepository<Owner, Integer>'],
    ['OwnerService', 'service/OwnerService.java', 'class OwnerService'],
    ['findByLastName', 'repository/OwnerRepository.java', 'List<Owner> findByLastName(String lastName)'],
    ['findOwnerById', 'service/OwnerService.java', 'Owner findOwnerById(int id)'],
    ['initFindForm', 'web/OwnerController.java', 'String initFindForm(Map<String, Object> model)'],
    ['processFindForm', 'web/OwnerController.java', 'String processFindForm(Owner owner)'],
    ['showOwner', 'web/OwnerController.java', 'ModelAndView showOwner(int ownerId)'],
    ['saveOwner', 'service/OwnerService.java', 'void saveOwner(Owner owner)'],
    ['addPet', 'model/Owner.java', 'void addPet(Pet pet)'],
    ['getPetsInternal', 'model/Owner.java', 'Set<Pet> getPetsInternal()'],
    ['getPet', 'model/Owner.java', 'Pet getPet(String name)'],
    ['getPets', 'model/Owner.java', 'List<Pet> getPets()'],
    ['processUpdateOwnerForm', 'web/OwnerController.java', 'String processUpdateOwnerForm(Owner owner)'],
    ['initUpdateOwnerForm', 'web/OwnerController.java', 'String initUpdateOwnerForm(int ownerId, Model model)'],
  ],
  'd-004': [
    ['SchedulerConfig', 'config/SchedulerConfig.java', 'class SchedulerConfig'],
    ['AppointmentService', 'service/AppointmentService.java', 'class AppointmentService'],
    ['AvailabilityChecker', 'service/AvailabilityChecker.java', 'class AvailabilityChecker'],
    ['AppointmentValidator', 'web/AppointmentValidator.java', 'class AppointmentValidator implements Validator'],
    ['checkAvailability', 'service/AvailabilityChecker.java', 'boolean checkAvailability(Vet vet, LocalDate date)'],
    ['bookAppointment', 'service/AppointmentService.java', 'Visit bookAppointment(Pet pet, Vet vet, LocalDate date)'],
    ['cancelAppointment', 'service/AppointmentService.java', 'void cancelAppointment(int visitId)'],
    ['validate', 'web/AppointmentValidator.java', 'void validate(Object obj, Errors errors)'],
    ['getAvailableSlots', 'service/AppointmentService.java', 'List<LocalDate> getAvailableSlots(int vetId)'],
    ['listUpcoming', 'service/AppointmentService.java', 'List<Visit> listUpcoming(int ownerId)'],
    ['sendReminder', 'service/AppointmentService.java', 'void sendReminder(Visit visit)'],
    ['conflictsWith', 'service/AvailabilityChecker.java', 'boolean conflictsWith(Visit a, Visit b)'],
  ],
  'd-005': [
    ['BaseEntity', 'model/BaseEntity.java', 'class BaseEntity implements Serializable'],
    ['NamedEntity', 'model/NamedEntity.java', 'class NamedEntity extends BaseEntity'],
    ['Person', 'model/Person.java', 'class Person extends NamedEntity'],
    ['JpaConfig', 'config/JpaConfig.java', 'class JpaConfig'],
    ['CacheConfig', 'config/CacheConfig.java', 'class CacheConfig'],
    ['getId', 'model/BaseEntity.java', 'Integer getId()'],
    ['setId', 'model/BaseEntity.java', 'void setId(Integer id)'],
    ['isNew', 'model/BaseEntity.java', 'boolean isNew()'],
    ['getName', 'model/NamedEntity.java', 'String getName()'],
    ['setName', 'model/NamedEntity.java', 'void setName(String name)'],
    ['getFirstName', 'model/Person.java', 'String getFirstName()'],
    ['getLastName', 'model/Person.java', 'String getLastName()'],
    ['DataSourceConfig', 'config/DataSourceConfig.java', 'class DataSourceConfig'],
    ['TransactionConfig', 'config/TransactionConfig.java', 'class TransactionConfig'],
    ['configureDataSource', 'config/DataSourceConfig.java', 'DataSource configureDataSource()'],
  ],
  'd-006': [
    ['GlobalExceptionHandler', 'web/GlobalExceptionHandler.java', 'class GlobalExceptionHandler'],
    ['WelcomeController', 'web/WelcomeController.java', 'class WelcomeController'],
    ['CrashController', 'web/CrashController.java', 'class CrashController'],
    ['handleError', 'web/GlobalExceptionHandler.java', 'ModelAndView handleError(HttpServletRequest req, Exception ex)'],
    ['welcome', 'web/WelcomeController.java', 'String welcome()'],
    ['triggerException', 'web/CrashController.java', 'String triggerException()'],
    ['resolveException', 'web/GlobalExceptionHandler.java', 'ModelAndView resolveException(Exception ex)'],
    ['handleConstraintViolation', 'web/GlobalExceptionHandler.java', 'ResponseEntity<Object> handleConstraintViolation(ConstraintViolationException ex)'],
    ['HealthController', 'web/HealthController.java', 'class HealthController'],
    ['checkHealth', 'web/HealthController.java', 'ResponseEntity<Map<String, Object>> checkHealth()'],
    ['ApiResponse', 'web/ApiResponse.java', 'class ApiResponse<T>'],
  ],
  'd-007': [
    ['WebMvcConfig', 'config/WebMvcConfig.java', 'class WebMvcConfig implements WebMvcConfigurer'],
    ['SecurityConfig', 'config/SecurityConfig.java', 'class SecurityConfig'],
    ['MvcConfig', 'config/MvcConfig.java', 'class MvcConfig extends WebMvcConfigurerAdapter'],
    ['addViewControllers', 'config/WebMvcConfig.java', 'void addViewControllers(ViewControllerRegistry registry)'],
    ['addResourceHandlers', 'config/WebMvcConfig.java', 'void addResourceHandlers(ResourceHandlerRegistry registry)'],
    ['configure', 'config/SecurityConfig.java', 'void configure(HttpSecurity http)'],
    ['extendMessageConverters', 'config/MvcConfig.java', 'void extendMessageConverters(List<HttpMessageConverter<?>> converters)'],
    ['corsConfigurer', 'config/WebMvcConfig.java', 'WebMvcConfigurer corsConfigurer()'],
    ['configureMessageConverters', 'config/WebMvcConfig.java', 'void configureMessageConverters(List<HttpMessageConverter<?>> converters)'],
  ],
  'd-008': [
    ['DateTimeUtil', 'util/DateTimeUtil.java', 'class DateTimeUtil'],
    ['StringUtils', 'util/StringUtils.java', 'class StringUtils'],
    ['ValidationUtils', 'util/ValidationUtils.java', 'class ValidationUtils'],
    ['formatDate', 'util/DateTimeUtil.java', 'String formatDate(LocalDate date, String pattern)'],
    ['parseDate', 'util/DateTimeUtil.java', 'LocalDate parseDate(String text, String pattern)'],
    ['capitalize', 'util/StringUtils.java', 'String capitalize(String str)'],
    ['isBlank', 'util/StringUtils.java', 'boolean isBlank(String str)'],
    ['hasErrors', 'util/ValidationUtils.java', 'boolean hasErrors(Errors errors, String field)'],
    ['rejectIfEmpty', 'util/ValidationUtils.java', 'void rejectIfEmpty(Errors errors, String field, String errorCode)'],
    ['truncate', 'util/StringUtils.java', 'String truncate(String str, int max)'],
  ],
  'd-009': [
    ['Article', 'domain/Article.java', 'class Article'],
    ['ArticleRepository', 'repository/ArticleRepository.java', 'interface ArticleRepository extends JpaRepository<Article, Long>'],
    ['ArticleService', 'service/ArticleService.java', 'class ArticleService'],
    ['ArticleController', 'api/ArticleController.java', 'class ArticleController'],
    ['Tag', 'domain/Tag.java', 'class Tag'],
    ['TagRepository', 'repository/TagRepository.java', 'interface TagRepository extends JpaRepository<Tag, Long>'],
    ['Comment', 'domain/Comment.java', 'class Comment'],
    ['CommentRepository', 'repository/CommentRepository.java', 'interface CommentRepository extends JpaRepository<Comment, Long>'],
    ['FavoriteRelationship', 'domain/FavoriteRelationship.java', 'class FavoriteRelationship'],
    ['createArticle', 'service/ArticleService.java', 'Article createArticle(String title, String body, User author)'],
    ['favoriteArticle', 'service/ArticleService.java', 'Article favoriteArticle(long id, User currentUser)'],
    ['findRecentArticles', 'repository/ArticleRepository.java', 'Page<Article> findRecentArticles(Pageable pageable)'],
    ['addComment', 'service/ArticleService.java', 'Comment addComment(long articleId, String body, User author)'],
    ['deleteArticle', 'service/ArticleService.java', 'void deleteArticle(String slug, User currentUser)'],
    ['updateArticle', 'service/ArticleService.java', 'Article updateArticle(String slug, UpdateArticleParam param, User currentUser)'],
    ['findBySlug', 'repository/ArticleRepository.java', 'Optional<Article> findBySlug(String slug)'],
    ['findByTagsContaining', 'repository/ArticleRepository.java', 'Page<Article> findByTagsContaining(String tag, Pageable pageable)'],
    ['deleteComment', 'service/ArticleService.java', 'void deleteComment(long articleId, long commentId, User currentUser)'],
    ['listArticleFeed', 'service/ArticleService.java', 'Page<Article> listArticleFeed(User currentUser, Pageable pageable)'],
  ],
  'd-010': [
    ['User', 'domain/User.java', 'class User'],
    ['UserRepository', 'repository/UserRepository.java', 'interface UserRepository extends JpaRepository<User, Long>'],
    ['UserService', 'service/UserService.java', 'class UserService'],
    ['ProfileController', 'api/ProfileController.java', 'class ProfileController'],
    ['FollowRelationship', 'domain/FollowRelationship.java', 'class FollowRelationship'],
    ['followUser', 'service/UserService.java', 'Profile followUser(String username, User currentUser)'],
    ['unfollowUser', 'service/UserService.java', 'Profile unfollowUser(String username, User currentUser)'],
    ['getProfile', 'service/UserService.java', 'Profile getProfile(String username, User currentUser)'],
    ['updateUser', 'service/UserService.java', 'User updateUser(UpdateUserParam param, User currentUser)'],
    ['findByEmail', 'repository/UserRepository.java', 'Optional<User> findByEmail(String email)'],
    ['findByUsername', 'repository/UserRepository.java', 'Optional<User> findByUsername(String username)'],
    ['updateBio', 'service/UserService.java', 'User updateBio(String username, String bio)'],
    ['isFollowing', 'service/UserService.java', 'boolean isFollowing(User follower, User target)'],
    ['getFollowers', 'service/UserService.java', 'List<User> getFollowers(String username)'],
  ],
  'd-011': [
    ['JwtTokenProvider', 'core/JwtTokenProvider.java', 'class JwtTokenProvider'],
    ['JwtTokenFilter', 'core/JwtTokenFilter.java', 'class JwtTokenFilter extends OncePerRequestFilter'],
    ['UserDetailsServiceImpl', 'service/UserDetailsServiceImpl.java', 'class UserDetailsServiceImpl implements UserDetailsService'],
    ['UserController', 'api/UserController.java', 'class UserController'],
    ['createToken', 'core/JwtTokenProvider.java', 'String createToken(String username)'],
    ['validateToken', 'core/JwtTokenProvider.java', 'boolean validateToken(String token)'],
    ['getUsername', 'core/JwtTokenProvider.java', 'String getUsername(String token)'],
    ['doFilterInternal', 'core/JwtTokenFilter.java', 'void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)'],
    ['loadUserByUsername', 'service/UserDetailsServiceImpl.java', 'UserDetails loadUserByUsername(String username)'],
    ['login', 'api/UserController.java', 'UserData login(LoginParam param)'],
    ['register', 'api/UserController.java', 'UserData register(RegisterParam param)'],
    ['getCurrentUser', 'api/UserController.java', 'UserData getCurrentUser(AuthenticationRequest authReq)'],
    ['updateCurrentUser', 'api/UserController.java', 'UserData updateCurrentUser(UpdateUserParam param)'],
    ['SecurityConfig', 'config/SecurityConfig.java', 'class SecurityConfig extends WebSecurityConfigurerAdapter'],
  ],
  'd-012': [
    ['Product', 'models/product.py', 'class Product(models.Model)'],
    ['Category', 'models/category.py', 'class Category(models.Model)'],
    ['ProductManager', 'models/product.py', 'class ProductManager(models.Manager)'],
    ['ProductListView', 'views/product_views.py', 'class ProductListView(ListView)'],
    ['ProductDetailView', 'views/product_views.py', 'class ProductDetailView(DetailView)'],
    ['CategoryView', 'views/category_views.py', 'class CategoryView(ListView)'],
    ['ProductSerializer', 'serializers/product_serializers.py', 'class ProductSerializer(serializers.ModelSerializer)'],
    ['get_available', 'models/product.py', 'def get_available(self)'],
    ['get_by_category', 'models/product.py', 'def get_by_category(cls, category_id)'],
    ['get_queryset', 'views/product_views.py', 'def get_queryset(self)'],
    ['get_context_data', 'views/product_views.py', 'def get_context_data(self, **kwargs)'],
    ['get_absolute_url', 'models/product.py', 'def get_absolute_url(self)'],
    ['to_representation', 'serializers/product_serializers.py', 'def to_representation(self, instance)'],
    ['CategorySerializer', 'serializers/category_serializers.py', 'class CategorySerializer(serializers.ModelSerializer)'],
    ['InventoryItem', 'models/inventory.py', 'class InventoryItem(models.Model)'],
    ['InventoryManager', 'models/inventory.py', 'class InventoryManager(models.Manager)'],
    ['decrease_stock', 'models/inventory.py', 'def decrease_stock(self, quantity)'],
    ['is_in_stock', 'models/inventory.py', 'def is_in_stock(self)'],
    ['ProductAPIView', 'views/product_api.py', 'class ProductAPIView(generics.ListAPIView)'],
  ],
};

function buildGraphData(): GraphData {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  let nodeIdx = 0;

  const domainNodeIds: Record<string, string[]> = {};

  for (const [domainId, templates] of Object.entries(NODE_TEMPLATES)) {
    const domain = MOCK_DOMAINS.find((d) => d.id === domainId);
    if (!domain) continue;
    domainNodeIds[domainId] = [];

    for (const [label, file, signature] of templates) {
      const id = `n-${String(++nodeIdx).padStart(3, '0')}`;
      nodes.push({ id, label, file, signature, domain: domain.name, domainId, degree: 0 });
      domainNodeIds[domainId].push(id);
    }
  }

  // Intra-domain edges — wire up realistic call patterns
  const intraEdges: [string, string, GraphEdge['type']][] = [
    // Pet Management
    ['n-003', 'n-004', 'calls'], ['n-003', 'n-005', 'calls'], ['n-001', 'n-002', 'uses'],
    ['n-005', 'n-004', 'calls'], ['n-006', 'n-001', 'uses'], ['n-008', 'n-014', 'calls'],
    ['n-010', 'n-008', 'calls'], ['n-011', 'n-006', 'calls'], ['n-012', 'n-004', 'calls'],
    ['n-013', 'n-004', 'calls'], ['n-014', 'n-004', 'calls'], ['n-015', 'n-004', 'calls'],
    ['n-016', 'n-003', 'calls'],
    // Veterinary Services
    ['n-019', 'n-020', 'calls'], ['n-019', 'n-021', 'calls'], ['n-022', 'n-023', 'calls'],
    ['n-021', 'n-020', 'calls'], ['n-023', 'n-022', 'calls'], ['n-026', 'n-027', 'calls'],
    ['n-025', 'n-020', 'calls'], ['n-028', 'n-023', 'calls'], ['n-029', 'n-021', 'calls'],
    ['n-030', 'n-019', 'calls'],
    // Owner Management
    ['n-032', 'n-033', 'calls'], ['n-032', 'n-034', 'calls'], ['n-034', 'n-033', 'calls'],
    ['n-035', 'n-033', 'calls'], ['n-036', 'n-034', 'calls'], ['n-037', 'n-034', 'calls'],
    ['n-038', 'n-034', 'calls'], ['n-039', 'n-034', 'calls'], ['n-040', 'n-034', 'calls'],
    // Cross-domain edges (controllers → services, services → repos)
    ['n-003', 'n-032', 'calls'], ['n-019', 'n-022', 'calls'],
    // Data access → base entities
    ['n-001', 'n-049', 'inherits'], ['n-017', 'n-049', 'inherits'], ['n-031', 'n-049', 'inherits'],
    ['n-050', 'n-049', 'inherits'],
  ];

  const degreeMap: Record<string, number> = {};

  for (const [source, target, type] of intraEdges) {
    // Only add if both nodes exist
    if (nodes.find((n) => n.id === source) && nodes.find((n) => n.id === target)) {
      edges.push({ source, target, type });
      degreeMap[source] = (degreeMap[source] ?? 0) + 1;
      degreeMap[target] = (degreeMap[target] ?? 0) + 1;
    }
  }

  // Generate additional edges to reach ~400 total
  const allIds = nodes.map((n) => n.id);
  let extraEdgeCount = 0;
  let i = 0;
  while (edges.length < 400 && i < 2000) {
    i++;
    const srcIdx = (extraEdgeCount * 7 + i * 3) % allIds.length;
    const tgtIdx = (extraEdgeCount * 11 + i * 5 + 1) % allIds.length;
    if (srcIdx === tgtIdx) continue;
    const src = allIds[srcIdx];
    const tgt = allIds[tgtIdx];
    if (!src || !tgt) continue;
    const alreadyExists = edges.some((e) => e.source === src && e.target === tgt);
    if (alreadyExists) continue;
    const edgeTypes: GraphEdge['type'][] = ['calls', 'calls', 'calls', 'imports', 'uses'];
    const type = edgeTypes[i % edgeTypes.length]!;
    edges.push({ source: src, target: tgt, type });
    degreeMap[src] = (degreeMap[src] ?? 0) + 1;
    degreeMap[tgt] = (degreeMap[tgt] ?? 0) + 1;
    extraEdgeCount++;
  }

  // Apply degree counts back to nodes
  for (const node of nodes) {
    node.degree = degreeMap[node.id] ?? 0;
  }

  return { nodes, edges };
}

export const MOCK_GRAPH_DATA: GraphData = buildGraphData();

// ─── Mock chat SSE events ──────────────────────────────────────────────────

const MOCK_RESPONSE =
  'The `apply_discount` function is called from three places in the codebase:\n\n' +
  '1. **`CheckoutService.processOrder`** — applies the discount after cart validation\n' +
  '2. **`PromotionController.applyPromoCode`** — called when a user submits a promo code\n' +
  '3. **`OrderService.recalculateTotal`** — re-applies discounts after an order is modified\n\n' +
  'The function signature is `apply_discount(order: Order, discount: Decimal) -> Order` ' +
  'and it mutates the order\'s `total_price` field in place, returning the modified order.';

const responseTokens = MOCK_RESPONSE.split(/(?<=\s)/);

export const MOCK_CHAT_EVENTS: ChatEvent[] = [
  { type: 'tool_call_start', tool: 'search_codebase', args: { query: 'apply_discount callers' }, id: 'tc-001' },
  { type: 'tool_call_end', id: 'tc-001', result: 'Found 3 call sites: CheckoutService.processOrder (line 87), PromotionController.applyPromoCode (line 42), OrderService.recalculateTotal (line 134)', durationMs: 312 },
  { type: 'tool_call_start', tool: 'get_function_context', args: { function_name: 'apply_discount' }, id: 'tc-002' },
  { type: 'tool_call_end', id: 'tc-002', result: 'def apply_discount(order: Order, discount: Decimal) -> Order:\n    order.total_price = order.subtotal * (1 - discount)\n    return order', durationMs: 198 },
  ...responseTokens.map((token): ChatEvent => ({ type: 'token', content: token })),
  { type: 'done' },
];

// ─── Temporary password helper ─────────────────────────────────────────────

export function generateTempPassword(): string {
  const chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$';
  return Array.from({ length: 16 }, (_, i) => chars[(i * 37 + 13) % chars.length]).join('');
}
